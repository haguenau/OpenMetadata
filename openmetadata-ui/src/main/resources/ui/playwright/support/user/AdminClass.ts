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
import { Page } from '@playwright/test';
import { DEFAULT_ADMIN_USER } from './user.constant';
import { UserClass } from './UserClass';

export class AdminClass extends UserClass {
  async login(
    page: Page,
    userName = DEFAULT_ADMIN_USER.userName,
    password = DEFAULT_ADMIN_USER.password
  ) {
    await super.login(page, userName, password);
  }
}
