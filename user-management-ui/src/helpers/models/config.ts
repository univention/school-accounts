// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {Formatter, Page, UGridRow} from '@univention/univention-veb';
import type {GlobalAction} from '@/helpers/models/interface';
import type {UserData} from '@/helpers/models/user';

export interface SchoolConfigResponseData {
  label: string;
  value: string;
  permissions: GlobalAction[];
}

export interface SchoolsConfigResponse {
  schools: SchoolConfigResponseData[];
}

export interface SchoolClassesConfigResponse {
  school_classes: GroupConfigResponseData[];
}

export interface WorkGroupsConfigResponse {
  work_groups: GroupConfigResponseData[];
}

export interface GroupConfigResponseData {
  label: string;
  value: string;
}

export interface SchoolConfigData {
  label: string;
  value: string;
  permissions: GlobalAction[];
}

export interface SchoolsConfig {
  schools: SchoolConfigData[];
}

export interface GroupConfig {
  columns: ColumnConfigData[];
  rows: UGridRow[];
}

export interface SchoolWorkGroupConfig {
  columns: ColumnConfigData[];
  rows: UGridRow[];
}

export interface ColumnConfigResponseData {
  label: string;
  attribute: string;
  order: number;
  sorting: 'asc' | 'dec' | 'none' | null;
  formatter: Formatter | null;
}

export interface ColumnsConfigResponse {
  columns: ColumnConfigResponseData[];
}

export interface ColumnConfigData {
  label: string;
  attribute: string;
  sorting?: 'asc' | 'dec' | 'none';
  formatter?: Formatter;
}

export interface ColumnsConfig {
  columns: ColumnConfigData[];
}

export interface FormConfig {
  pages: Page[];
}

export type AddViewResponse = FormConfig;
export type AddViewConfig = FormConfig;

export interface EditViewResponse extends FormConfig {
  id: string;
  user: UserData;
}

export interface EditViewConfig extends FormConfig {
  id: string;
  user: UserData;
}
