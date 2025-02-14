/*
 *  Copyright 2024 Collate.
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *  http://www.apache.org/licenses/LICENSE-2.0
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
import { APIRequestContext } from '@playwright/test';
import { uuid } from '../../utils/common';
type ResponseDataType = {
  name: string;
  displayName: string;
  description: string;
  teamType: string;
  id?: string;
  fullyQualifiedName?: string;
};

export class TeamClass {
  id = uuid();
  data: ResponseDataType;
  responseData: ResponseDataType;

  constructor(data?: ResponseDataType) {
    this.data = data ?? {
      name: `PW%team-${this.id}`,
      displayName: `PW Team ${this.id}`,
      description: 'playwright team description',
      teamType: 'Group',
    };
  }

  setTeamType(teamType: string) {
    this.data.teamType = teamType;
  }

  get() {
    return this.responseData;
  }

  async create(apiContext: APIRequestContext) {
    const response = await apiContext.post('/api/v1/teams', {
      data: this.data,
    });
    const data = await response.json();
    this.responseData = data;

    return this.responseData;
  }

  async delete(apiContext: APIRequestContext) {
    const response = await apiContext.delete(
      `/api/v1/teams/${this.responseData.id}?hardDelete=true&recursive=false`
    );

    return response.body;
  }
}
