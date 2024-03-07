// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {InMemoryDB} from '@/helpers/models/db';
import {makeMockAddConfig, makeMockColumnsConfig, makeMockEditConfig} from '@/helpers/mocks/config';

export const mockDbData: Record<string, InMemoryDB> = {
  emptyData: {
    schoolsConfig: [],
    columnsConfig: [],
    addFormConfig: {pages: []},
    editFormConfig: {pages: []},
    classes: [],
    users: [],
  },
  testDefaultData: {
    schoolsConfig: [
      {
        label: 'School 1',
        value: 'school1',
        permissions: ['add'],
      },
      {
        label: 'School 2',
        value: 'school2',
        permissions: [],
      },
    ],
    columnsConfig: makeMockColumnsConfig(),
    addFormConfig: makeMockAddConfig(),
    editFormConfig: makeMockEditConfig(),
    classes: [
      {
        id: 'school1_class1',
        school: 'school1',
        attributes: {
          classname: {
            value: 'school1:class1',
            access: 'read',
          },
        },
      },
      {
        id: 'school1_class2',
        school: 'school1',
        attributes: {
          classname: {
            value: 'school1:class2',
            access: 'read',
          },
        },
      },
      {
        id: 'school2_class1',
        school: 'school2',
        attributes: {
          classname: {
            value: 'school2:class1',
            access: 'read',
          },
        },
      },
      {
        id: 'school2_class2',
        school: 'school2',
        attributes: {
          classname: {
            value: 'school2:class2',
            access: 'read',
          },
        },
      },
    ],
    users: [
      {
        id: 'test1.student1',
        allowedActions: ['delete'],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student1',
          },
          firstname: {
            access: 'read',
            value: 'Test1',
          },
          lastname: {
            access: 'read',
            value: 'Student1',
          },
          roles: {
            access: 'none',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'none',
            value: ['school1_class1'],
          },
          schools: {
            access: 'read',
            value: ['school1'],
          },
          active: {
            access: 'read',
            value: false,
          },
        },
      },
      {
        id: 'test1.student2',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student2',
          },
          firstname: {
            access: 'read',
            value: 'Test1',
          },
          lastname: {
            access: 'read',
            value: 'Student2',
          },
          roles: {
            access: 'read',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'read',
            value: ['school1_class2'],
          },
          schools: {
            access: 'read',
            value: ['school1'],
          },
          active: {
            access: 'read',
            value: true,
          },
        },
      },
      {
        id: 'test1.student3',
        allowedActions: ['delete'],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student3',
          },
          firstname: {
            access: 'read',
            value: 'Test1',
          },
          lastname: {
            access: 'read',
            value: 'Student3',
          },
          roles: {
            access: 'read',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'read',
            value: ['school1_class1'],
          },
          schools: {
            access: 'read',
            value: ['school1'],
          },
          active: {
            access: 'read',
            value: true,
          },
        },
      },
      {
        id: 'test1.student4',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student4',
          },
          firstname: {
            access: 'read',
            value: 'Test1',
          },
          lastname: {
            access: 'read',
            value: 'Student4',
          },
          roles: {
            access: 'read',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'read',
            value: ['school1_class1'],
          },
          schools: {
            access: 'read',
            value: ['school1'],
          },
          active: {
            access: 'read',
            value: true,
          },
        },
      },
      {
        id: 'test2.student1',
        allowedActions: ['delete'],
        attributes: {
          username: {
            access: 'read',
            value: 'test2.student1',
          },
          firstname: {
            access: 'read',
            value: 'Test2',
          },
          lastname: {
            access: 'read',
            value: 'Student1',
          },
          roles: {
            access: 'none',
            value: ['student:school:school2'],
          },
          classes: {
            access: 'none',
            value: ['school2_class1'],
          },
          schools: {
            access: 'read',
            value: ['school2'],
          },
          active: {
            access: 'read',
            value: false,
          },
        },
      },
      {
        id: 'test2.student2',
        allowedActions: ['delete'],
        attributes: {
          username: {
            access: 'read',
            value: 'test2.student2',
          },
          firstname: {
            access: 'read',
            value: 'Test2',
          },
          lastname: {
            access: 'read',
            value: 'Student2',
          },
          roles: {
            access: 'read',
            value: ['student:school:school2'],
          },
          classes: {
            access: 'read',
            value: ['school2_class2'],
          },
          schools: {
            access: 'read',
            value: ['school2'],
          },
          active: {
            access: 'read',
            value: true,
          },
        },
      },
    ],
  },
  noPermissions: {
    schoolsConfig: [
      {
        label: 'School 1',
        value: 'school1',
        permissions: [],
      },
    ],
    columnsConfig: makeMockColumnsConfig(),
    addFormConfig: makeMockAddConfig({
      username: 'none',
      lastname: 'none',
      firstname: 'none',
      password: 'none',
      classes: 'none',
      roles: 'none',
      active: 'none',
    }),
    editFormConfig: makeMockEditConfig({
      username: 'read',
      lastname: 'none',
      firstname: 'none',
      password: 'none',
      classes: 'none',
      roles: 'none',
      active: 'none',
    }),
    classes: [
      {
        id: 'school1:class1',
        school: 'school1',
        attributes: {
          classname: {
            value: 'school1:class1',
            access: 'read',
          },
        },
      },
      {
        id: 'school1:class2',
        school: 'school1',
        attributes: {
          classname: {
            value: 'school1:class2',
            access: 'read',
          },
        },
      },
    ],
    users: [
      {
        id: 'test1.student1',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student1',
          },
          firstname: {
            access: 'none',
            value: 'Test1',
          },
          lastname: {
            access: 'none',
            value: 'Student1',
          },
          roles: {
            access: 'none',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'none',
            value: ['school1_class1'],
          },
          schools: {
            access: 'none',
            value: ['school1'],
          },
          active: {
            access: 'none',
            value: false,
          },
        },
      },
      {
        id: 'test1.student2',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student2',
          },
          firstname: {
            access: 'none',
            value: 'Test1',
          },
          lastname: {
            access: 'none',
            value: 'Student2',
          },
          roles: {
            access: 'none',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'none',
            value: ['school1_class2'],
          },
          schools: {
            access: 'none',
            value: ['school1'],
          },
          active: {
            access: 'none',
            value: true,
          },
        },
      },
      {
        id: 'test1.student3',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student3',
          },
          firstname: {
            access: 'none',
            value: 'Test1',
          },
          lastname: {
            access: 'none',
            value: 'Student3',
          },
          roles: {
            access: 'none',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'none',
            value: ['school1_class1'],
          },
          schools: {
            access: 'none',
            value: ['school1'],
          },
          active: {
            access: 'none',
            value: true,
          },
        },
      },
      {
        id: 'test1.student4',
        allowedActions: [],
        attributes: {
          username: {
            access: 'read',
            value: 'test1.student4',
          },
          firstname: {
            access: 'none',
            value: 'Test1',
          },
          lastname: {
            access: 'none',
            value: 'Student4',
          },
          roles: {
            access: 'none',
            value: ['student:school:school1'],
          },
          classes: {
            access: 'none',
            value: ['school1_class1'],
          },
          schools: {
            access: 'none',
            value: ['school1'],
          },
          active: {
            access: 'none',
            value: true,
          },
        },
      },
    ],
  },
};
