// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';
import {type AuthenticationPort} from '@univention/univention-veb';
import {type DataPort} from '@/ports/data';
import {errorToString} from '@/helpers/error';
import {type Result} from '@/helpers/models/http';
import {
  type School,
  type SchoolsResponse,
  type SchoolResponseData,
  type WrappedSchoolsList,
} from '@/helpers/models/school';
import {type User, type UsersResponse, type UserResponseData, type WrappedUsersList} from '@/helpers/models/user';
import {
  type UserColumn,
  type UserColumnsResponse,
  type UserColumnResponseData,
  type WrappedUserColumnsList,
} from '@/helpers/models/userColumn';
import {makeMockSchools, makeMockSchoolsResponse} from '@/helpers/mocks/school';
import {makeMockUsers, makeMockUsersResponse} from '@/helpers/mocks/user';
import {makeMockUserColumns, makeMockUserColumnsResponse} from '@/helpers/mocks/userColumn';

class GenericDataAdapter implements DataPort {
  async fetchSchoolsConfig(): Promise<Result<WrappedSchoolsList, string>> {
    const result = await this.fetchSchoolsConfigRequest();
    if (!result.ok) {
      return result;
    }
    return {
      ok: true,
      value: {
        schools: result.value.schools.map(school => this._schoolFromApi(school)),
      },
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

  async fetchUserColumns(): Promise<Result<WrappedUserColumnsList, string>> {
    const result = await this.fetchUserColumnsRequest();
    if (!result.ok) {
      return result;
    }
    result.value.columns.sort((a, b) => {
      return a.order - b.order;
    });
    return {
      ok: true,
      value: {
        columns: result.value.columns.map(column => this._userColumnFromApi(column)),
      },
    };
  }

  async removeUser(id: string): Promise<Result<null, string>> {
    return await this.removeUserRequest(id);
  }

  removeUserRequest(id: string): Promise<Result<null, string>> {
    throw new Error(`Not Implemented. id=${id};`);
  }

  _schoolFromApi(schoolData: SchoolResponseData): School {
    return {
      label: schoolData.label,
      value: schoolData.value,
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

  _userColumnFromApi(userColumnData: UserColumnResponseData): UserColumn {
    const columnBase: UserColumn = {
      label: userColumnData.label,
      attribute: userColumnData.attribute,
    };
    if (userColumnData.sorting !== null) {
      columnBase.sorting = userColumnData.sorting;
    }
    if (userColumnData.formatter !== null) {
      columnBase.formatter = userColumnData.formatter;
    }
    return columnBase;
  }

  fetchSchoolsConfigRequest(): Promise<Result<SchoolsResponse, string>> {
    throw new Error('Not Implemented');
  }

  fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    throw new Error(`Not Implemented: school=${school}`);
  }

  fetchUserColumnsRequest(): Promise<Result<UserColumnsResponse, string>> {
    throw new Error('Not Implemented');
  }
}

interface InMemoryDB {
  schools: SchoolResponseData[];
  users: UserResponseData[];
  userColumns: UserColumnResponseData[];
}

export class InMemoryDataAdapter extends GenericDataAdapter {
  private readonly _responseTimeout = 1000;

  private _db: InMemoryDB = {
    schools: [],
    users: [],
    userColumns: [],
  };

  constructor(dbData?: InMemoryDB) {
    super();
    if (dbData) {
      this._db = dbData;
    } else {
      this._db.schools = makeMockSchools();
      this._db.users = makeMockUsers();
      this._db.userColumns = makeMockUserColumns();
    }
  }

  async fetchSchoolsConfigRequest(): Promise<Result<SchoolsResponse, string>> {
    const response = makeMockSchoolsResponse(this._db.schools);
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

  async fetchUserColumnsRequest(): Promise<Result<UserColumnsResponse, string>> {
    const response = makeMockUserColumnsResponse(this._db.userColumns);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: response,
        });
      }, this._responseTimeout);
    });
  }

  removeUserRequest(id: string): Promise<Result<null, string>> {
    const existingUser = this._db.users.find(user => user.id === id);

    if (existingUser) {
      const index = this._db.users.indexOf(existingUser);
      this._db.users.splice(index, 1);
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

  async fetchSchoolsConfigRequest(): Promise<Result<SchoolsResponse, string>> {
    return await this._get<SchoolsResponse>('/config-schools');
  }

  async fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    return await this._get<UsersResponse>(`/users?school=${school}`);
  }

  async fetchUserColumnsRequest(): Promise<Result<UserColumnsResponse, string>> {
    return await this._get<UserColumnsResponse>('/config-users');
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

  async _fetchToJson<T>(endpointBase: string, httpMethod: string): Promise<Result<T, string>> {
    const result = await this._fetch(endpointBase, httpMethod);
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

  async _fetch(endpointBase: string, httpMethod: string): Promise<Result<Response, string>> {
    const url = this._makeUrl(endpointBase);
    const headers = await this._makeHeaders();
    const result = await this._tryFn(() => fetch(url, {method: httpMethod, headers: headers}));
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

  async _parseError(response: Response): Promise<string | null> {
    if (!response.ok) {
      const text = (await response.text()) || response.statusText;
      let detail = text;
      try {
        const json = JSON.parse(text);
        if (json && typeof json === 'object' && 'detail' in json) {
          detail = json.detail;
        }
      } catch (err) {
        // Either not a JSON response, or unparsable. We'll just ignore this.
      }
      return `${response.status}: ${detail}`;
    }

    return null;
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
