// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

export interface SchoolResponseData {
  label: string;
  value: string;
}

export interface SchoolsResponse {
  schools: SchoolResponseData[];
}

export interface School {
  label: string;
  value: string;
}

export interface WrappedSchoolsList {
  schools: School[];
}
