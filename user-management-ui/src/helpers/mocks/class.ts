// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {SchoolClass} from '@/helpers/models/class';
import {schools} from '@/helpers/mocks/config';

export const classes = ['1a', '1b', '2a', '2b', '3a', '3b', '4a', '4b'];

export const makeClassId = (classname: string, school: string): string => {
  return `${school}_${classname}`;
};

export const makeMockClasses = () => {
  const schoolClasses: SchoolClass[] = [];
  for (const school of schools) {
    for (const classname of classes) {
      schoolClasses.push({
        id: makeClassId(classname, school),
        school: school,
        attributes: {
          classname: {
            value: classname,
            access: 'read',
          },
        },
      });
    }
  }
  return schoolClasses;
};
