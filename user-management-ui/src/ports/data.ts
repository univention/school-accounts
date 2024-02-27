// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type Result} from '@/helpers/models/http';
import {type WrappedSchoolsList} from '@/helpers/models/school';
import {type WrappedUsersList} from '@/helpers/models/user';
import {type WrappedUserColumnsList} from '@/helpers/models/userColumn';

export const dataPortSetting = 'userManagementUi.adapter.dataPort';

export interface DataPort {
  fetchSchoolsConfig(): Promise<Result<WrappedSchoolsList, string>>;
  fetchUsers(school: string): Promise<Result<WrappedUsersList, string>>;
  fetchUserColumns(): Promise<Result<WrappedUserColumnsList, string>>;
}
