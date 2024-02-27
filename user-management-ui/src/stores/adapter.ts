// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {defineStore} from 'pinia';
import {InvalidAdapterError} from '@univention/univention-veb';
import {type SettingsConfig} from '@/helpers/models/stores/settings';
import {type DataPort} from '@/ports/data';
import {InMemoryDataAdapter} from '@/adapters/data';

export const useAdapterStore = (config: SettingsConfig) => {
  return defineStore('adapter', () => {
    const dataAdapter: DataPort = (() => {
      const portSetting = config.dataPort.adapter;
      switch (portSetting) {
        case 'in_memory':
          return new InMemoryDataAdapter();
        default:
          throw new InvalidAdapterError(`Invalid data adapter: ${portSetting}`);
      }
    })();

    return {
      dataAdapter,
    };
  })();
};
