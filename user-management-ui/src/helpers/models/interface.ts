// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type User} from '@/helpers/models/user';
import {type SchoolResponseData} from '@/helpers/models/school';
import {type UserColumn} from '@/helpers/models/userColumn';
import {type UGridRow} from '@univention/univention-veb';

type FormValues = Record<string, any>;

interface UserConfig {
  columns: UserColumn[];
}

export interface ListViewConfig {
  schools: SchoolResponseData[];
  users: UserConfig;
}

interface UserState {
  searchFormValues: FormValues;
  rowSelection: string[];
  rows: User[];
}

export interface ListViewState {
  users: UserState;
}

export interface GridRow extends UGridRow {
  allowedActions: string[];
}
