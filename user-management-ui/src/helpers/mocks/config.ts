// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';
import type {Field, FieldMultiSelect, FieldSelect} from '@univention/univention-veb';
import type {
  AddViewResponse,
  ColumnsConfigResponse,
  ColumnConfigResponseData,
  EditViewResponse,
  FormConfig,
  SchoolConfigData,
  SchoolsConfigResponse,
  SchoolConfigResponseData,
} from '@/helpers/models/config';
import type {SchoolClass} from '@/helpers/models/class';
import type {User, UserData} from '@/helpers/models/user';

export const schools = ['school-1', 'school-2', 'school-3', 'school-4', 'school-5'];

export const makeMockSchoolsConfig = (): SchoolConfigResponseData[] => {
  const schoolsConfig: SchoolConfigResponseData[] = [];
  for (const school of schools) {
    schoolsConfig.push({
      label: `School ${school.split('-')[1]}`,
      value: school,
      permissions: Math.floor(Math.random() * 3) ? ['add'] : [],
    });
  }
  return schoolsConfig;
};

export const makeMockSchoolsConfigResponse = (schoolsConfig: SchoolConfigResponseData[]): SchoolsConfigResponse => {
  return {
    schools: schoolsConfig,
  };
};

export const makeMockColumnsConfig = (): ColumnConfigResponseData[] => {
  const columnsConfig: ColumnConfigResponseData[] = [
    {
      label: i18next.t('mocks.formConfig.field.lastname'),
      attribute: 'lastname',
      sorting: 'asc',
      order: 1,
      formatter: null,
    },
    {
      label: i18next.t('mocks.formConfig.field.firstname'),
      attribute: 'firstname',
      sorting: 'asc',
      order: 2,
      formatter: null,
    },
    {
      label: i18next.t('mocks.formConfig.field.username'),
      attribute: 'username',
      order: 3,
      sorting: null,
      formatter: null,
    },
    {
      label: i18next.t('mocks.formConfig.field.roles.label'),
      attribute: 'roles',
      order: 4,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: i18next.t('mocks.formConfig.field.classes'),
      attribute: 'classes',
      order: 5,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: i18next.t('mocks.formConfig.field.schools'),
      attribute: 'schools',
      order: 6,
      sorting: null,
      formatter: {
        type: 'list',
      },
    },
    {
      label: i18next.t('mocks.formConfig.field.active'),
      attribute: 'active',
      order: 7,
      sorting: null,
      formatter: {
        type: 'boolean',
      },
    },
  ];
  return columnsConfig;
};

export const makeMockColumnsConfigResponse = (columnsConfig: ColumnConfigResponseData[]): ColumnsConfigResponse => {
  return {
    columns: columnsConfig,
  };
};

type AccessConfig = Record<string, 'read' | 'write' | 'none'>;

export const makeMockAddConfig = (accessConfig?: AccessConfig): FormConfig => {
  const access = accessConfig || {};
  return {
    pages: [
      {
        label: i18next.t('mocks.formConfig.page.name.add'),
        name: 'useradd',
        fieldsets: [
          {
            label: i18next.t('mocks.formConfig.fieldset.name'),
            name: 'userinfo',
            rows: [
              [
                {
                  type: 'UComboBox',
                  props: {
                    label: i18next.t('mocks.formConfig.field.school'),
                    name: 'school',
                    required: true,
                    access: access.school || 'read',
                    options: [],
                  },
                },
              ],
              [
                {
                  type: 'UInputText',
                  props: {
                    label: i18next.t('mocks.formConfig.field.lastname'),
                    name: 'lastname',
                    required: true,
                    access: access.lastname || 'write',
                  },
                },
                {
                  type: 'UInputText',
                  props: {
                    label: i18next.t('mocks.formConfig.field.firstname'),
                    name: 'firstname',
                    required: true,
                    access: access.firstname || 'write',
                  },
                },
              ],
              {
                type: 'UInputText',
                props: {
                  label: i18next.t('mocks.formConfig.field.username'),
                  name: 'username',
                  required: true,
                  access: access.username || 'write',
                },
              },
              {
                type: 'UInputPassword',
                props: {
                  label: i18next.t('mocks.formConfig.field.password'),
                  name: 'password',
                  required: false,
                  access: access.password || 'write',
                },
              },
              {
                type: 'UMultiSelect',
                props: {
                  label: i18next.t('mocks.formConfig.field.classes'),
                  name: 'classes',
                  required: false,
                  access: access.classes || 'write',
                  columns: [
                    {
                      label: i18next.t('mocks.formConfig.field.class'),
                      attribute: 'classname',
                    },
                  ],
                  rows: [],
                },
              },
              {
                type: 'UMultiSelect',
                props: {
                  label: i18next.t('mocks.formConfig.field.roles.label'),
                  name: 'roles',
                  required: true,
                  access: access.roles || 'write',
                  columns: [
                    {
                      label: i18next.t('mocks.formConfig.field.role'),
                      attribute: 'name',
                    },
                  ],
                  rows: [
                    {
                      id: 'student',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.student'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'teacher',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.teacher'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'staff',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.staff'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'administrator',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.administrator'),
                          access: 'read',
                        },
                      },
                    },
                  ],
                },
              },
              {
                type: 'UInputCheckbox',
                props: {
                  label: i18next.t('mocks.formConfig.field.active'),
                  name: 'active',
                  required: false,
                  access: access.active || 'write',
                },
              },
            ],
          },
        ],
      },
    ],
  };
};

export const makeMockEditConfig = (accessConfig?: AccessConfig): FormConfig => {
  const access = accessConfig || {};
  return {
    pages: [
      {
        label: i18next.t('mocks.formConfig.page.name.edit'),
        name: 'useredit',
        fieldsets: [
          {
            label: i18next.t('mocks.formConfig.fieldset.name'),
            name: 'userinfo',
            rows: [
              {
                type: 'UComboBox',
                props: {
                  label: i18next.t('mocks.formConfig.field.school'),
                  name: 'school',
                  required: true,
                  access: access.school || 'read',
                  options: [],
                },
              },
              [
                {
                  type: 'UInputText',
                  props: {
                    label: i18next.t('mocks.formConfig.field.lastname'),
                    name: 'lastname',
                    required: true,
                    access: access.lastname || 'write',
                  },
                },
                {
                  type: 'UInputText',
                  props: {
                    label: i18next.t('mocks.formConfig.field.firstname'),
                    name: 'firstname',
                    required: true,
                    access: access.firstname || 'write',
                  },
                },
              ],
              {
                type: 'UInputText',
                props: {
                  label: i18next.t('mocks.formConfig.field.username'),
                  name: 'username',
                  required: false,
                  access: access.username || 'write',
                },
              },
              {
                type: 'UInputPassword',
                props: {
                  label: i18next.t('mocks.formConfig.field.password'),
                  name: 'password',
                  required: false,
                  access: access.password || 'none',
                },
              },
              {
                type: 'UMultiSelect',
                props: {
                  label: i18next.t('mocks.formConfig.field.classes'),
                  name: 'classes',
                  access: access.classes || 'write',
                  columns: [
                    {
                      label: i18next.t('mocks.formConfig.field.class'),
                      attribute: 'classname',
                    },
                  ],
                  rows: [],
                },
              },
              {
                type: 'UMultiSelect',
                props: {
                  label: i18next.t('mocks.formConfig.field.roles.label'),
                  name: 'roles',
                  required: true,
                  access: access.roles || 'read',
                  columns: [
                    {
                      label: i18next.t('mocks.formConfig.field.role'),
                      attribute: 'name',
                    },
                  ],
                  rows: [
                    {
                      id: 'student',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.student'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'teacher',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.teacher'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'staff',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.staff'),
                          access: 'read',
                        },
                      },
                    },
                    {
                      id: 'administrator',
                      attributes: {
                        name: {
                          value: i18next.t('mocks.formConfig.field.roles.options.administrator'),
                          access: 'read',
                        },
                      },
                    },
                  ],
                },
              },
              {
                type: 'UInputCheckbox',
                props: {
                  label: i18next.t('mocks.formConfig.field.active'),
                  name: 'active',
                  required: false,
                  access: access.active || 'read',
                },
              },
            ],
          },
        ],
      },
    ],
  };
};

const findField = (fieldName: string, formConfig: FormConfig): Field | null => {
  for (const page of formConfig.pages) {
    for (const fieldset of page.fieldsets) {
      for (const row of fieldset.rows) {
        const fields: Field[] = Array.isArray(row) ? row : [row];
        for (const field of fields) {
          if (field.props.name === fieldName) {
            return field;
          }
        }
      }
    }
  }
  return null;
};

const updateConfig = (formConfig: FormConfig, schools: SchoolConfigData[], classes: SchoolClass[]): FormConfig => {
  const config = JSON.parse(JSON.stringify(formConfig)) as FormConfig;

  const schoolField = findField('school', config) as FieldSelect;
  if (schoolField) {
    for (const school of schools) {
      schoolField.props.options.push({
        label: school.label,
        value: school.value,
      });
    }
  }

  const classesField = findField('classes', config) as FieldMultiSelect;
  if (classesField) {
    for (const schoolClass of classes) {
      classesField.props.rows.push({
        id: schoolClass.id,
        attributes: schoolClass.attributes,
      });
    }
  }

  return config;
};

export const makeMockAddConfigResponse = (
  schools: SchoolConfigData[],
  classes: SchoolClass[],
  formConfig: FormConfig
): AddViewResponse => {
  const config = updateConfig(formConfig, schools, classes);
  return config;
};

export const makeMockEditConfigResponse = (
  user: User,
  school: string,
  schools: SchoolConfigData[],
  classes: SchoolClass[],
  formConfig: FormConfig
): EditViewResponse => {
  const config = updateConfig(formConfig, schools, classes);

  const userData: UserData = {};
  for (const key in user.attributes) {
    const schoolAttrs = ['schools', 'roles', 'classes'];
    if (schoolAttrs.includes(key)) {
      switch (key) {
        case 'schools':
          userData['school'] = school;
          break;
        case 'roles':
          userData[key] = (user.attributes[key].value as string[])
            .filter(userRole => (userRole.split(':')[2] || '') === school)
            .map(userRole => userRole.split(':', 1)[0]);
          break;
        case 'classes':
          userData[key] = (user.attributes[key].value as string[]).filter(
            userClass => (userClass.split('_', 1)[0] || '') === school
          );
          break;
      }
    } else {
      userData[key] = user.attributes[key].value;
    }
  }
  // Fill out any extra data that isn't in the user
  for (const page of config.pages) {
    for (const fieldset of page.fieldsets) {
      for (let row of fieldset.rows) {
        if (!Array.isArray(row)) {
          row = [row];
        }
        for (const field of row) {
          if (userData[field.props.name] === 'undefined') {
            userData[field.props.name] = null;
          }
        }
      }
    }
  }

  return {
    id: user.id || '',
    user: userData,
    ...config,
  };
};
