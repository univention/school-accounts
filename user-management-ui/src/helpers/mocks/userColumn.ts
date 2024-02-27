// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type UserColumnsResponse, type UserColumnResponseData} from '@/helpers/models/userColumn';

export const makeMockUserColumns = (): UserColumnResponseData[] => {
  const userColumns: UserColumnResponseData[] = [
    {
      label: 'Last Name',
      attribute: 'lastname',
      sorting: 'asc',
      order: 1,
      formatter: null,
    },
    {
      label: 'First Name',
      attribute: 'firstname',
      sorting: 'asc',
      order: 2,
      formatter: null,
    },
    {
      label: 'Username',
      attribute: 'username',
      order: 3,
      sorting: null,
      formatter: null,
    },
    {
      label: 'Roles',
      attribute: 'roles',
      order: 4,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: 'Classes',
      attribute: 'classes',
      order: 5,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: 'Schools',
      attribute: 'schools',
      order: 6,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: 'Active',
      attribute: 'active',
      order: 7,
      sorting: null,
      formatter: {
        type: 'boolean',
      },
    },
  ];
  return userColumns;
};

export const makeMockUserColumnsResponse = (userColumns: UserColumnResponseData[]): UserColumnsResponse => {
  return {
    columns: userColumns,
  };
};
