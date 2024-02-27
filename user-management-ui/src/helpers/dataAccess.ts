// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {errorToString} from '@/helpers/error';
import {type ListViewConfig} from '@/helpers/models/interface';
import {type Result} from '@/helpers/models/http';
import {type WrappedUsersList} from '@/helpers/models/user';
import {type DataPort} from '@/ports/data';
import {useAdapterStore} from '@/stores/adapter';
import {useSettingsStore} from '@/stores/settings';

const getDataAdapter = async (): Promise<DataPort> => {
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
  let dataAdapter: DataPort | null = null;
  try {
    dataAdapter = await getDataAdapter();
  } catch (err: unknown) {
    return {
      ok: false,
      error: errorToString(err),
    };
  }

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
