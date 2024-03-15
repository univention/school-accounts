// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {User} from '@/helpers/models/user';
import type {ColumnsConfig, SchoolConfigData} from '@/helpers/models/config';
import {type UGridRow} from '@univention/univention-veb';

export type GlobalAction = 'add';

type FormValues = Record<string, any>;

export interface ListViewConfig {
  schools: SchoolConfigData[];
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
