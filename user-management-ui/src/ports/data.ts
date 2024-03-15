// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {FetchObjectError, Result, SaveError} from '@/helpers/models/http';
import type {AddViewConfig, EditViewConfig, ColumnsConfig, SchoolsConfig} from '@/helpers/models/config';
import type {UserData, WrappedUser, WrappedUsersList} from '@/helpers/models/user';

export const dataPortSetting = 'userManagementUi.adapter.dataPort';

export interface DataPort {
  fetchSchoolsConfig(): Promise<Result<SchoolsConfig, string>>;
  fetchListViewConfig(): Promise<Result<ColumnsConfig, string>>;
  fetchAddViewConfig(school: string): Promise<Result<AddViewConfig, string>>;
  fetchEditViewConfig(id: string, school: string): Promise<Result<EditViewConfig, FetchObjectError>>;

  fetchUsers(school: string): Promise<Result<WrappedUsersList, string>>;

  createUser(school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>>;
  updateUser(id: string, school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>>;
  removeUser(id: string): Promise<Result<null, string>>;
}
