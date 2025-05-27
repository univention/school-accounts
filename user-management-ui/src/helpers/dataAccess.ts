// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {AddViewConfig, ColumnsConfig, EditViewConfig, SchoolsConfig} from '@/helpers/models/config';
import type {FetchObjectError, Result, SaveError} from '@/helpers/models/http';
import type {FormValues, ListViewConfig} from '@/helpers/models/interface';
import type {WrappedUser, WrappedUsersList} from '@/helpers/models/user';
import type {DataPort} from '@/ports/data';
import {useAdapterStore} from '@/stores/adapter';
import {useSettingsStore} from '@/stores/settings';

export const getDataAdapter = async (): Promise<DataPort> => {
  const settingsStore = useSettingsStore();
  await settingsStore.init();
  const adapterStore = useAdapterStore(settingsStore.config);
  return adapterStore.dataAdapter;
};

export const getUsers = async (
  school: string,
  schoolClasses: string[],
  workGroups: string[]
): Promise<Result<WrappedUsersList, string>> => {
  const dataAdapter = await getDataAdapter();
  const usersResult = await dataAdapter.fetchUsers(school, schoolClasses, workGroups);
  return usersResult;
};

export const getListViewConfig = async (): Promise<Result<ListViewConfig, string>> => {
  const dataAdapter = await getDataAdapter();

  const [schoolsConfigResult, columnsConfigResult]: [Result<SchoolsConfig, string>, Result<ColumnsConfig, string>] =
    await Promise.all([dataAdapter.fetchSchoolsConfig(), dataAdapter.fetchListViewConfig()]);
  if (!schoolsConfigResult.ok) {
    return schoolsConfigResult;
  }
  if (!columnsConfigResult.ok) {
    return columnsConfigResult;
  }

  const school = schoolsConfigResult.value.schools[0].value;

  const [schoolClassesConfigResult, workGroupConfigResult] = await Promise.all([
    dataAdapter.fetchSchoolClassConfig(school),
    dataAdapter.fetchWorkGroupConfig(school),
  ]);

  if (!schoolClassesConfigResult.ok) {
    return schoolClassesConfigResult;
  }
  if (!workGroupConfigResult.ok) {
    return workGroupConfigResult;
  }

  return {
    ok: true,
    value: {
      schools: schoolsConfigResult.value.schools,
      groups: {
        schoolClasses: {
          columns: schoolClassesConfigResult.value.columns,
          rows: schoolClassesConfigResult.value.rows,
        },
        workGroups: {
          columns: workGroupConfigResult.value.columns,
          rows: workGroupConfigResult.value.rows,
        },
      },
      users: {
        columns: columnsConfigResult.value.columns,
      },
    },
  };
};

export const fetchAddViewConfig = async (school: string): Promise<Result<AddViewConfig, string>> => {
  const dataAdapter = await getDataAdapter();
  return dataAdapter.fetchAddViewConfig(school);
};

export const fetchEditViewConfig = async (
  id: string,
  school: string
): Promise<Result<EditViewConfig, FetchObjectError>> => {
  const dataAdapter = await getDataAdapter();
  return dataAdapter.fetchEditViewConfig(id, school);
};

export const createUser = async (school: string, values: FormValues): Promise<Result<WrappedUser, SaveError>> => {
  const dataAdapter = await getDataAdapter();
  return dataAdapter.createUser(school, values);
};

export const updateUser = async (
  id: string,
  school: string,
  values: FormValues
): Promise<Result<WrappedUser, SaveError>> => {
  const dataAdapter = await getDataAdapter();
  return dataAdapter.updateUser(id, school, values);
};

export const deleteUsers = async (ids: string[]): Promise<{id: string; error: string}[]> => {
  const dataAdapter = await getDataAdapter();
  const results = await Promise.all(ids.map(id => dataAdapter.removeUser(id)));
  const errors = results.map(result => (result.ok ? null : result.error));
  const fails: {id: string; error: string}[] = [];
  for (let x = 0; x < results.length; x++) {
    const error = errors[x];
    if (error) {
      fails.push({
        id: ids[x],
        error,
      });
    }
  }
  return fails;
};
