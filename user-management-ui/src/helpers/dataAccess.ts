// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type ListViewConfig} from '@/helpers/models/interface';
import {type Result} from '@/helpers/models/http';
import {type WrappedUsersList} from '@/helpers/models/user';
import {type DataPort} from '@/ports/data';
import {useAdapterStore} from '@/stores/adapter';
import {useSettingsStore} from '@/stores/settings';

export const getDataAdapter = async (): Promise<DataPort> => {
  const settingsStore = useSettingsStore();
  await settingsStore.init();
  const adapterStore = useAdapterStore(settingsStore.config);
  return adapterStore.dataAdapter;
};

export const getUsers = async (school: string): Promise<Result<WrappedUsersList, string>> => {
  const dataAdapter = await getDataAdapter();
  const usersResult = await dataAdapter.fetchUsers(school);
  return usersResult;
};

export const getListViewConfig = async (): Promise<Result<ListViewConfig, string>> => {
  const dataAdapter = await getDataAdapter();

  const schoolsResult = await dataAdapter.fetchSchoolsConfig();
  if (!schoolsResult.ok) {
    return schoolsResult;
  }
  const columnConfigResult = await dataAdapter.fetchUserColumns();
  if (!columnConfigResult.ok) {
    return columnConfigResult;
  }

  return {
    ok: true,
    value: {
      schools: schoolsResult.value.schools,
      users: {
        columns: columnConfigResult.value.columns,
      },
    },
  };
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
