// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type DataPort} from '@/ports/data';
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
  async fetchSchoolsSearch(): Promise<Result<WrappedSchoolsList, string>> {
    const result = await this.fetchSchoolsSearchRequest();
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

  fetchSchoolsSearchRequest(): Promise<Result<SchoolsResponse, string>> {
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

  fetchSchoolsSearchRequest(): Promise<Result<SchoolsResponse, string>> {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: makeMockSchoolsResponse(this._db.schools),
        });
      }, this._responseTimeout);
    });
  }

  fetchUsersRequest(school: string): Promise<Result<UsersResponse, string>> {
    const users = this._db.users.filter(user => {
      const userSchools = user.attributes.schools.value as string[];
      return userSchools.includes(school);
    });
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: makeMockUsersResponse(users),
        });
      }, this._responseTimeout);
    });
  }

  fetchUserColumnsRequest(): Promise<Result<UserColumnsResponse, string>> {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          value: makeMockUserColumnsResponse(this._db.userColumns),
        });
      }, this._responseTimeout);
    });
  }
}
