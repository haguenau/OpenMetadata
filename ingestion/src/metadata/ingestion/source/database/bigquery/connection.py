#  Copyright 2021 Collate
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Source connection handler
"""
import os
from datetime import datetime, timezone
from functools import partial
from typing import Optional

from google.cloud.datacatalog_v1 import PolicyTagManagerClient
from sqlalchemy.engine import Engine

from metadata.generated.schema.entity.automations.workflow import (
    Workflow as AutomationWorkflow,
)
from metadata.generated.schema.entity.services.connections.database.bigQueryConnection import (
    BigQueryConnection,
)
from metadata.generated.schema.security.credentials.gcpValues import (
    GcpCredentialsValues,
    MultipleProjectId,
    SingleProjectId,
)
from metadata.ingestion.connections.builders import (
    create_generic_db_connection,
    get_connection_args_common,
)
from metadata.ingestion.connections.test_connections import (
    execute_inspector_func,
    test_connection_engine_step,
    test_connection_steps,
    test_query,
)
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.bigquery.queries import BIGQUERY_TEST_STATEMENT
from metadata.utils.credentials import set_google_credentials
from metadata.utils.logger import ingestion_logger

logger = ingestion_logger()


def get_connection_url(connection: BigQueryConnection) -> str:
    """
    Build the connection URL and set the project
    environment variable when needed
    """

    if isinstance(connection.credentials.gcpConfig, GcpCredentialsValues):
        if isinstance(  # pylint: disable=no-else-return
            connection.credentials.gcpConfig.projectId, SingleProjectId
        ):
            if not connection.credentials.gcpConfig.projectId.root:
                return f"{connection.scheme.value}://{connection.credentials.gcpConfig.projectId or ''}"
            if (
                not connection.credentials.gcpConfig.privateKey
                and connection.credentials.gcpConfig.projectId.root
            ):
                project_id = connection.credentials.gcpConfig.projectId.root
                os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            return f"{connection.scheme.value}://{connection.credentials.gcpConfig.projectId.root}"
        elif isinstance(connection.credentials.gcpConfig.projectId, MultipleProjectId):
            for project_id in connection.credentials.gcpConfig.projectId.root:
                if not connection.credentials.gcpConfig.privateKey and project_id:
                    # Setting environment variable based on project id given by user / set in ADC
                    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
                return f"{connection.scheme.value}://{project_id}"
            return f"{connection.scheme.value}://"

    return f"{connection.scheme.value}://"


def get_connection(connection: BigQueryConnection) -> Engine:
    """
    Prepare the engine and the GCP credentials
    """
    set_google_credentials(gcp_credentials=connection.credentials)
    return create_generic_db_connection(
        connection=connection,
        get_connection_url_fn=get_connection_url,
        get_connection_args_fn=get_connection_args_common,
    )


def test_connection(
    metadata: OpenMetadata,
    engine: Engine,
    service_connection: BigQueryConnection,
    automation_workflow: Optional[AutomationWorkflow] = None,
) -> None:
    """
    Test connection. This can be executed either as part
    of a metadata workflow or during an Automation Workflow
    """

    def get_tags(taxonomies):
        for taxonomy in taxonomies:
            policy_tags = PolicyTagManagerClient().list_policy_tags(
                parent=taxonomy.name
            )
            return policy_tags

    def test_tags():
        taxonomy_project_ids = []
        if engine.url.host:
            taxonomy_project_ids.append(engine.url.host)
        if service_connection.taxonomyProjectID:
            taxonomy_project_ids.extend(service_connection.taxonomyProjectID)
        if not taxonomy_project_ids:
            logger.info("'taxonomyProjectID' is not set, so skipping this test.")
            return None

        taxonomy_location = service_connection.taxonomyLocation
        if not taxonomy_location:
            logger.info("'taxonomyLocation' is not set, so skipping this test.")
            return None

        taxonomies = []
        for project_id in taxonomy_project_ids:
            taxonomies.extend(
                PolicyTagManagerClient().list_taxonomies(
                    parent=f"projects/{project_id}/locations/{taxonomy_location}"
                )
            )
        return get_tags(taxonomies)

    def test_connection_inner(engine):
        test_fn = {
            "CheckAccess": partial(test_connection_engine_step, engine),
            "GetSchemas": partial(execute_inspector_func, engine, "get_schema_names"),
            "GetTables": partial(execute_inspector_func, engine, "get_table_names"),
            "GetViews": partial(execute_inspector_func, engine, "get_view_names"),
            "GetTags": test_tags,
            "GetQueries": partial(
                test_query,
                engine=engine,
                statement=BIGQUERY_TEST_STATEMENT.format(
                    region=service_connection.usageLocation,
                    creation_date=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
                ),
            ),
        }

        test_connection_steps(
            metadata=metadata,
            test_fn=test_fn,
            service_type=service_connection.type.value,
            automation_workflow=automation_workflow,
        )

    test_connection_inner(engine)
