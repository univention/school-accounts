// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {User} from '@/helpers/models/user';
import type {ColumnsConfig, GroupConfig, SchoolConfigData} from '@/helpers/models/config';
import {type UGridRow} from '@univention/univention-veb';

export type GlobalAction = 'add';

export type FormValues = Record<string, any>;

export interface ListViewConfig {
  schools: SchoolConfigData[];
  groups: {
    schoolClasses: GroupConfig;
    workGroups: GroupConfig;
  };
  users: ColumnsConfig;
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
