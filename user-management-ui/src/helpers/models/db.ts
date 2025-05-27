// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {
  ColumnConfigResponseData,
  FormConfig,
  GroupConfigResponseData,
  SchoolConfigResponseData,
} from '@/helpers/models/config';
import type {SchoolClass} from '@/helpers/models/class';
import type {UserResponseData} from '@/helpers/models/user';

export interface InMemoryDB {
  schoolsConfig: SchoolConfigResponseData[];
  schoolClassesConfig: GroupConfigResponseData[];
  workGroupsConfig: GroupConfigResponseData[];
  columnsConfig: ColumnConfigResponseData[];
  addFormConfig: FormConfig;
  editFormConfig: FormConfig;
  classes: SchoolClass[];
  users: UserResponseData[];
}
