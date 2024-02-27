// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type SchoolsResponse, type SchoolResponseData} from '@/helpers/models/school';

export const makeMockSchools = (): SchoolResponseData[] => {
  const numSchools: number = 5;
  const schools: SchoolResponseData[] = [];
  for (let x = 1; x <= numSchools; x++) {
    schools.push({
      label: `School ${x}`,
      value: `school-${x}`,
    });
  }
  return schools;
};

export const makeMockSchoolsResponse = (schools: SchoolResponseData[]): SchoolsResponse => {
  return {
    schools: schools,
  };
};
