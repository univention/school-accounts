// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type Formatter} from '@univention/univention-veb';

export interface UserColumnResponseData {
  label: string;
  attribute: string;
  order: number;
  sorting: 'asc' | 'dec' | 'none' | null;
  formatter: Formatter | null;
}

export interface UserColumnsResponse {
  columns: UserColumnResponseData[];
}

export interface UserColumn {
  label: string;
  attribute: string;
  sorting?: 'asc' | 'dec' | 'none';
  formatter?: Formatter;
}

export interface WrappedUserColumnsList {
  columns: UserColumn[];
}
