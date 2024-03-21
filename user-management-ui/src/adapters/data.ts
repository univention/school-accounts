// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';
import type {AuthenticationPort, Field, Fieldset, Page} from '@univention/univention-veb';
import type {DataPort} from '@/ports/data';
import {errorToString} from '@/helpers/error';
import type {InMemoryDB} from '@/helpers/models/db';
import type {FetchObjectError, FieldError, Result, SaveError} from '@/helpers/models/http';
import type {
  AddViewConfig,
  AddViewResponse,
  ColumnConfigData,
  ColumnsConfig,
  ColumnConfigResponseData,
  ColumnsConfigResponse,
  EditViewConfig,
  EditViewResponse,
  SchoolConfigData,
  SchoolsConfig,
  SchoolsConfigResponse,
  SchoolConfigResponseData,
} from '@/helpers/models/config';
import type {
  User,
  UserData,
  UserResponse,
  UsersResponse,
  UserResponseData,
  WrappedUser,
  WrappedUsersList,
} from '@/helpers/models/user';
import {
  makeMockAddConfig,
  makeMockAddConfigResponse,
  makeMockColumnsConfig,
  makeMockColumnsConfigResponse,
  makeMockEditConfig,
  makeMockEditConfigResponse,
  makeMockSchoolsConfig,
  makeMockSchoolsConfigResponse,
} from '@/helpers/mocks/config';
import {makeMockClasses} from '@/helpers/mocks/class';
import {makeMockUsers, makeMockUsersResponse, makeRole} from '@/helpers/mocks/user';

class GenericDataAdapter implements DataPort {
  async fetchSchoolsConfig(): Promise<Result<SchoolsConfig, string>> {
    const result = await this.fetchSchoolsConfigRequest();
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: {
        schools: result.value.schools.map(school => this._schoolConfigFromApi(school)),
      },
    };
  }

  async fetchListViewConfig(): Promise<Result<ColumnsConfig, string>> {
    const result = await this.fetchListViewConfigRequest();
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: this._listViewConfigFromApi(result.value),
    };
  }

  async fetchAddViewConfig(school: string): Promise<Result<AddViewConfig, string>> {
    const result = await this.fetchAddViewConfigRequest(school);
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: this._addViewConfigFromApi(result.value),
    };
  }

  async fetchEditViewConfig(id: string, school: string): Promise<Result<EditViewConfig, FetchObjectError>> {
    const result = await this.fetchEditViewConfigRequest(id, school);
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: this._editViewConfigFromApi(result.value),
    };
  }

  async fetchUsers(school: string): Promise<Result<WrappedUsersList, string>> {
    const result = await this.fetchUsersRequest(school);
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: {
        users: result.value.users.map(user => this._userFromApi(user)),
      },
    };
  }

  async createUser(school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>> {
    const result = await this.createUserRequest(school, userData);
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: {
        user: this._userFromApi(result.value.user),
      },
    };
  }

  async updateUser(id: string, school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>> {
    const result = await this.updateUserRequest(id, school, userData);
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: {
        user: this._userFromApi(result.value.user),
      },
    };
  }

  async removeUser(id: string): Promise<Result<null, string>> {
    return await this.removeUserRequest(id);
  }

  _columnConfigFromApi(columnConfig: ColumnConfigResponseData): ColumnConfigData {
    const columnBase: ColumnConfigData = {
      label: columnConfig.label,
      attribute: columnConfig.attribute,
    };

    // The univention-veb library does not currently handle null values in these fields;
    // however the backend needs to send them.
    // We need to remove these from the response that gets sent to the frontend.
    if (columnConfig.sorting !== null) {
      columnBase.sorting = columnConfig.sorting;
    }
    if (columnConfig.formatter !== null) {
      columnBase.formatter = columnConfig.formatter;
    }

    return columnBase;
  }

  _pageFromApi(pageResponse: Page): Page {
    const page: Page = {
      label: pageResponse.label,
      name: pageResponse.name,
      fieldsets: [],
    };
    for (const fieldsetResponse of pageResponse.fieldsets) {
      const fieldset: Fieldset = {
        label: fieldsetResponse.label,
        name: fieldsetResponse.name,
        rows: [],
      };

      for (const rowResponse of fieldsetResponse.rows) {
        const row = Array.isArray(rowResponse) ? rowResponse : [rowResponse];
        const fields: Field[] = [];

        for (const fieldResponse of row) {
          const field: Field = {
            type: fieldResponse.type,
            props: JSON.parse(JSON.stringify(fieldResponse.props)),
          };
          if (fieldResponse.type === 'UMultiSelect') {
            // @ts-ignore -- We already checked that this is a UMultiSelect
            field.props.columns = fieldResponse.props.columns.map((column: ColumnConfigResponseData) =>
              this._columnConfigFromApi(column)
            );
          } else if (fieldResponse.type === 'UMultiObjectSelect') {
            // @ts-ignore -- We already checked that this is a UMultiObjectSelect
            field.props.columns = fieldResponse.props.columns.map((column: ColumnConfigResponseData) =>
              this._columnConfigFromApi(column)
            );
            // @ts-ignore -- We already checked that this is a UMultiObjectSelect
            field.props.searchColumns = fieldResponse.props.searchColumns.map((column: ColumnConfigResponseData) =>
              this._columnConfigFromApi(column)
            );
          }

          fields.push(field);
        }

        fieldset.rows.push(fields);
      }

      page.fieldsets.push(fieldset);
    }
    return page;
  }

  _schoolConfigFromApi(schoolData: SchoolConfigResponseData): SchoolConfigData {
    return {
      label: schoolData.label,
      value: schoolData.value,
      permissions: schoolData.permissions,
    };
  }

  _listViewConfigFromApi(columnsConfigResponse: ColumnsConfigResponse): ColumnsConfig {
    columnsConfigResponse.columns.sort((a, b) => {
      return a.order - b.order;
    });

    const columns = columnsConfigResponse.columns.map(columnConfig => this._columnConfigFromApi(columnConfig));
    return {columns};
  }

  _addViewConfigFromApi(addViewResponse: AddViewResponse): AddViewConfig {
    return {
      pages: addViewResponse.pages.map(page => this._pageFromApi(page)),
    };
  }

  _editViewConfigFromApi(editViewResponse: EditViewResponse): EditViewConfig {
    return {
      id: editViewResponse.id,
      user: editViewResponse.user,
      pages: editViewResponse.pages.map(page => this._pageFromApi(page)),
    };
  }

  _userFromApi(userData: UserResponseData): User {
    const userBase: User = {
      id: userData.id,
      attributes: {},
      allowedActions: userData.allowedActions,
    };
    for (const [key, attr] of Object.entries(userData.attributes)) {
      userBase.attributes[key] = {
        access: attr.access,
        value: attr.value,
      };
    }
    return userBase;
  }

  fetchSchoolsConfigRequest(): Promise<Result<SchoolsConfigResponse, string>> {
    throw new Error('Not Implemented');
  }

  fetchListViewConfigRequest(): Promise<Result<ColumnsConfigResponse, string>> {
    throw new Error('Not Implemented');
  }

  fetchAddViewConfigRequest(school: string): Promise<Result<AddViewResponse, string>> {
    throw new Error(`Not Implemented. school=${school}`);
  }

  fetchEditViewConfigRequest(id: string, school: string): Promise<Result<EditViewResponse, FetchObjectError>> {
    throw new Error(`Not Implemented. id=${id} school=${school}`);
  }

  fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    throw new Error(`Not Implemented. school=${school}`);
  }

  createUserRequest(school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    throw new Error(`Not Implemented. school=${school} userData=${userData}`);
  }

  updateUserRequest(id: string, school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    throw new Error(`Not Implemented. id=${id} school=${school} userData=${userData}`);
  }

  removeUserRequest(id: string): Promise<Result<null, string>> {
    throw new Error(`Not Implemented. id=${id};`);
  }
}

export const inMemoryDataAdapterSettings = {
  dbData: 'inMemoryDataAdapter.dbData',
};

export class InMemoryDataAdapter extends GenericDataAdapter {
  private readonly _responseTimeout = 1000;

  private _db: InMemoryDB = {
    schoolsConfig: [],
    columnsConfig: [],
    addFormConfig: {pages: []},
    editFormConfig: {pages: []},
    classes: [],
    users: [],
  };

  constructor(dbData?: InMemoryDB) {
    super();
    if (dbData) {
      this._db = dbData;
    } else {
      this._db.schoolsConfig = makeMockSchoolsConfig();
      this._db.columnsConfig = makeMockColumnsConfig();
      this._db.addFormConfig = makeMockAddConfig();
      this._db.editFormConfig = makeMockEditConfig();
      this._db.classes = makeMockClasses();
      this._db.users = makeMockUsers();
    }
  }

  async fetchSchoolsConfigRequest(): Promise<Result<SchoolsConfigResponse, string>> {
    const response = makeMockSchoolsConfigResponse(this._db.schoolsConfig);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  async fetchListViewConfigRequest(): Promise<Result<ColumnsConfigResponse, string>> {
    const response = makeMockColumnsConfigResponse(this._db.columnsConfig);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  fetchAddViewConfigRequest(school: string): Promise<Result<AddViewResponse, string>> {
    const classes = this._db.classes.filter(schoolClass => schoolClass.school === school);
    const response = makeMockAddConfigResponse(this._db.schoolsConfig, classes, this._db.addFormConfig);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  fetchEditViewConfigRequest(id: string, school: string): Promise<Result<EditViewResponse, FetchObjectError>> {
    const mockUser = this._db.users.find(user => user.id === id);
    if (!mockUser) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'objectNotFound',
            },
          });
        });
      });
    }

    const classes = this._db.classes.filter(schoolClass => schoolClass.school === school);
    const response = makeMockEditConfigResponse(
      mockUser,
      school,
      this._db.schoolsConfig,
      classes,
      this._db.editFormConfig
    );
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  async fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    const users = this._db.users.filter(user => {
      const userSchools = user.attributes.schools.value as string[];
      return userSchools.includes(school);
    });
    const response = makeMockUsersResponse(users);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  async createUserRequest(school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    let username = userData.username;
    if (!username || username === '') {
      const base = `${userData.firstname}.${userData.lastname}`;
      const suffix = Math.floor(Math.random() * 1000) + 100;
      username = `${base}${suffix}`;
    }

    const existingUser = this._db.users.filter(user => user.id === username)[0];
    if (existingUser) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'generic',
              message: '400: object already exists',
            },
          });
        }, this._responseTimeout);
      });
    }

    const user: User = {
      id: username,
      allowedActions: ['delete'],
      attributes: {},
    };
    for (const key in userData) {
      let value = userData[key];

      if (key === 'school') {
        user.attributes['schools'] = {
          access: 'read',
          value: [value],
        };
      } else {
        if (key === 'roles') {
          const roles: string[] = [];
          const school = userData.school || '';
          for (const role of userData[key]) {
            roles.push(makeRole(role, school));
          }
          value = roles;
        } else if (key == 'username') {
          value = username;
        }

        user.attributes[key] = {
          access: 'read',
          value: value,
        };
      }
    }
    this._db.users.push(user);

    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: {user},
        });
      }, this._responseTimeout);
    });
  }

  async updateUserRequest(id: string, school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    const existingUser = this._db.users.filter(user => user.id === id)[0];
    if (!existingUser) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'objectNotFound',
            },
          });
        }, this._responseTimeout);
      });
    }

    for (const key in userData) {
      const existingValue = existingUser.attributes[key].value;
      let value = userData[key];

      if (key === 'school') {
        // Do nothing; we can't modify schools
      } else {
        if (key === 'roles') {
          const existingRoles = (existingValue as string[]).filter(role => (role.split(':')[2] || '') !== school);

          const roles: string[] = [];
          const school = userData.school || '';
          for (const role of userData[key]) {
            roles.push(makeRole(role, school));
          }
          value = roles.concat(existingRoles);
        } else if (key === 'classes') {
          const existingClasses = (existingValue as string[]).filter(
            userClass => (userClass.split('_')[0] || '') !== school
          );
          value = value.concat(existingClasses);
        }

        existingUser.attributes[key] = {
          access: 'read',
          value: value,
        };
        if (key === 'username') {
          existingUser.id = value;
        }
      }
    }

    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: {
            user: existingUser,
          },
        });
      }, this._responseTimeout);
    });
  }

  async removeUserRequest(id: string): Promise<Result<null, string>> {
    const existingUser = this._db.users.find(user => user.id === id);

    if (existingUser) {
      if (existingUser.allowedActions.includes('delete')) {
        const index = this._db.users.indexOf(existingUser);
        this._db.users.splice(index, 1);
      } else {
        return {
          ok: false,
          error: '403: Permission denied',
        };
      }
    }
    // We don't check for a non existingUser.
    // We treat deleting non-existent objects as a success.

    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: null,
        });
      }, this._responseTimeout);
    });
  }
}

export const apiDataSettings = {
  uri: 'apiDataAdapter.uri',
};

export class ApiDataAdapter extends GenericDataAdapter {
  private readonly _apiUri: string;
  private readonly _authAdapter: AuthenticationPort;

  constructor(apiUri: string, authAdapter: AuthenticationPort) {
    super();
    this._authAdapter = authAdapter;

    // Remove a trailing slash, if one exists,
    // so we always create a correct URL.
    const url = apiUri.replace(/\/$/, '');
    this._apiUri = url;
  }

  async fetchSchoolsConfigRequest(): Promise<Result<SchoolsConfigResponse, string>> {
    return await this._get<SchoolsConfigResponse>('/config/schools');
  }

  async fetchListViewConfigRequest(): Promise<Result<ColumnsConfigResponse, string>> {
    return await this._get<ColumnsConfigResponse>('/config/users/list');
  }

  async fetchAddViewConfigRequest(school: string): Promise<Result<AddViewResponse, string>> {
    const schoolParam = encodeURIComponent(school);
    return await this._get<AddViewResponse>(`/config/users/add?school=${schoolParam}`);
  }

  async fetchEditViewConfigRequest(id: string, school: string): Promise<Result<EditViewResponse, FetchObjectError>> {
    const idParam = encodeURIComponent(id);
    const schoolParam = encodeURIComponent(school);

    const result = await this._get<EditViewResponse>(`/config/users/edit?id=${idParam}&school=${schoolParam}`);
    if (!result.ok) {
      return {
        ok: false,
        error: this._parseFetchObjectError(result.error),
      };
    }

    return result;
  }

  async fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    return await this._get<UsersResponse>(`/users?school=${school}`);
  }

  async createUserRequest(school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    const schoolParam = encodeURIComponent(school);
    return await this._save<UserResponse>(`/users?school=${schoolParam}`, userData, 'post');
  }

  async updateUserRequest(id: string, school: string, userData: UserData): Promise<Result<UserResponse, SaveError>> {
    const idParam = encodeURIComponent(id);
    const schoolParam = encodeURIComponent(school);
    return await this._save<UserResponse>(`/users/${idParam}?school=${schoolParam}`, userData, 'patch');
  }

  async removeUserRequest(id: string): Promise<Result<null, string>> {
    const result = await this._fetch(`/users/${id}`, 'DELETE');
    if (!result.ok) {
      return result;
    }

    const error = await this._parseError(result.value);
    if (error) {
      return {
        ok: false,
        error,
      };
    }

    return {
      ok: true,
      value: null,
    };
  }

  _makeUrl(endpoint: string): string {
    return `${this._apiUri}${endpoint}`;
  }

  async _makeHeaders(): Promise<Record<string, string>> {
    const authHeader = await this._authAdapter.getValidAuthorizationHeader();
    const defaultHeaders = {
      'Accept-Language': i18next.language,
      accept: 'application/json',
      'Content-Type': 'application/json;charset=UTF-8',
    };
    return {
      ...defaultHeaders,
      ...authHeader,
    };
  }

  async _fetchToJson<T>(endpointBase: string, httpMethod: string, body?: unknown): Promise<Result<T, string>> {
    const result = await this._fetch(endpointBase, httpMethod, body);
    if (!result.ok) {
      return result;
    }

    const error = await this._parseError(result.value);
    if (error) {
      return {
        ok: false,
        error,
      };
    }

    return await this._tryToJson<T>(result.value);
  }

  async _fetch(endpointBase: string, httpMethod: string, body?: unknown): Promise<Result<Response, string>> {
    const url = this._makeUrl(endpointBase);
    const headers = await this._makeHeaders();

    let result: Result<Response, string> | null = null;
    if (body !== undefined) {
      const bodyJson = JSON.stringify(body);
      result = await this._tryFn(() => fetch(url, {method: httpMethod, headers: headers, body: bodyJson}));
    } else {
      result = await this._tryFn(() => fetch(url, {method: httpMethod, headers: headers}));
    }

    if (!result.ok) {
      return {
        ok: false,
        error: i18next.t('ApiDataAdapter.fetchFailed', {
          method: httpMethod,
          msg: result.error,
        }),
      };
    }
    return result;
  }

  async _get<T>(endpointBase: string): Promise<Result<T, string>> {
    return await this._fetchToJson<T>(endpointBase, 'GET');
  }

  async _patch<T>(endpointBase: string, body: any): Promise<Result<T, string>> {
    return await this._fetchToJson<T>(endpointBase, 'PATCH', body);
  }

  async _post<T>(endpointBase: string, body: any): Promise<Result<T, string>> {
    return await this._fetchToJson<T>(endpointBase, 'POST', body);
  }

  async _parseError(response: Response): Promise<string | null> {
    if (!response.ok) {
      const text = (await response.text()) || response.statusText;
      let detail = text;
      try {
        const json = JSON.parse(text);
        // Most errors are going to be in a simple format with just a `detail` key.
        // Anything more complex, and we'll just go with the original response text.
        if (json && typeof json === 'object' && 'detail' in json && Object.keys(json).length === 1) {
          detail = JSON.stringify(json.detail);
        }
      } catch (err) {
        // Either not a JSON response, or unparsable. We'll just ignore this.
      }
      return `${response.status}: ${detail}`;
    }

    return null;
  }

  _parseFetchObjectError(error: string): FetchObjectError {
    const statusCode = error.split(':', 1)[0].trim();
    if (statusCode === '404') {
      return {
        type: 'objectNotFound',
      };
    }

    const errorText = error.split(':').slice(1).join(':').trim();
    return {
      type: 'generic',
      message: errorText,
    };
  }

  _parseSaveError(error: string): SaveError {
    const statusCode = error.split(':', 1)[0].trim();
    if (statusCode === '404') {
      return {
        type: 'objectNotFound',
      };
    }

    let errorText = error.split(':').slice(1).join(':').trim();
    if (statusCode === '403' || statusCode === '422') {
      try {
        const errorJson = JSON.parse(errorText);

        if (statusCode === '403') {
          return {
            type: 'permissionsError',
            message: errorJson.detail || '',
            missingPermissions: errorJson.missingPermissions || [],
          };
        } else {
          if (Array.isArray(errorJson)) {
            const error: SaveError = {
              type: 'fieldErrors',
              errors: [],
            };
            for (const detail of errorJson) {
              const err = detail as FieldError;
              const field = err.loc[err.loc.length - 1];
              if (field) {
                error.errors.push({
                  field,
                  message: err.msg,
                });
              }
            }
            return error;
          }
        }
      } catch (err) {
        // JSON parse error or misc error.
        // Just return original error so we get the full information.
        errorText = error;
      }
    }

    // Returned for 400 status, unexpected statuses, and JSON parse errors
    return {
      type: 'generic',
      message: errorText,
    };
  }

  async _save<T>(endpointBase: string, body: any, method: 'post' | 'patch'): Promise<Result<T, SaveError>> {
    const _method = {
      post: this._post,
      patch: this._patch,
    }[method].bind(this);

    const result = await _method<T>(endpointBase, body);
    if (!result.ok) {
      return {
        ok: false,
        error: this._parseSaveError(result.error),
      };
    }

    return result;
  }

  async _tryFn<T>(fn: () => Promise<T>): Promise<Result<T, string>> {
    try {
      const value = await fn();
      return {
        ok: true,
        value,
      };
    } catch (err: unknown) {
      return {
        ok: false,
        error: errorToString(err),
      };
    }
  }

  async _tryToJson<T>(response: Response): Promise<Result<T, string>> {
    const result = await this._tryFn(() => response.json());
    if (!result.ok) {
      return {
        ok: false,
        error: i18next.t('ApiDataAdapter.jsonError', {msg: result.error}),
      };
    }

    // TODO: Add run-time checks that `result.value` is of type `T`
    // response.json() returns `any` as type so the type check against `T` will
    // always work but might actually be wrong.
    // Add run-time checks
    return result;
  }
}

export const testDataAdapterSettings = {
  subAdapter: 'testDataAdapter.subAdapter',
  errorResponses: 'testDataAdapter.errorResponses',
};

export class TestDataAdapter implements DataPort {
  private readonly _responseTimeout = 1000;

  _adapter: DataPort;
  _errorResponses: Map<string, string>;

  constructor(adapter: DataPort, errorResponses?: Map<string, string>) {
    this._adapter = adapter;
    this._errorResponses = errorResponses || new Map();
  }

  async fetchSchoolsConfig(): Promise<Result<SchoolsConfig, string>> {
    const errResponse = this._errorResponses.get('fetchSchoolsConfig');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: errResponse,
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.fetchSchoolsConfig();
  }

  async fetchListViewConfig(): Promise<Result<ColumnsConfig, string>> {
    const errResponse = this._errorResponses.get('fetchListViewConfig');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: errResponse,
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.fetchListViewConfig();
  }

  async fetchAddViewConfig(school: string): Promise<Result<AddViewConfig, string>> {
    const errResponse = this._errorResponses.get('fetchAddViewConfig');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: errResponse,
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.fetchAddViewConfig(school);
  }

  async fetchEditViewConfig(id: string, school: string): Promise<Result<EditViewConfig, FetchObjectError>> {
    const errResponse = this._errorResponses.get('fetchEditViewConfig');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'generic',
              message: errResponse,
            },
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.fetchEditViewConfig(id, school);
  }

  async fetchUsers(school: string): Promise<Result<WrappedUsersList, string>> {
    const errResponse = this._errorResponses.get('fetchUsers');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: errResponse,
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.fetchUsers(school);
  }

  async createUser(school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>> {
    const errResponse = this._errorResponses.get('createUser');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'generic',
              message: errResponse,
            },
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.createUser(school, userData);
  }

  async updateUser(id: string, school: string, userData: UserData): Promise<Result<WrappedUser, SaveError>> {
    const errResponse = this._errorResponses.get('updateUser');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: {
              type: 'generic',
              message: errResponse,
            },
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.updateUser(id, school, userData);
  }

  async removeUser(id: string): Promise<Result<null, string>> {
    const errResponse = this._errorResponses.get('removeUser');
    if (errResponse !== undefined) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: false,
            error: errResponse,
          });
        }, this._responseTimeout);
      });
    }
    return await this._adapter.removeUser(id);
  }
}
