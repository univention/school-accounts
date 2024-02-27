// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {defineStore} from 'pinia';
import {ref} from 'vue';
import {EnvSettingsAdapter, InvalidAdapterError, type SettingsPort} from '@univention/univention-veb';
import {dataPortSetting} from '@/ports/data';
import {apiDataSettings} from '@/adapters/data';
import {type SettingsConfig} from '@/helpers/models/stores/settings';

export const useSettingsStore = defineStore('settings', () => {
  const initialized = ref(false);

  const config = ref<SettingsConfig>({
    settingsPort: {
      adapter: '',
    },
    dataPort: {
      adapter: '',
      apiConfig: {
        uri: '',
      },
    },
  });

  const init = async (
    adapterName: string = import.meta.env.VITE__USER_MANAGEMENT_UI__ADAPTER__SETTINGS_PORT,
    forceReinitialize = false
  ): Promise<void> => {
    // Don't take the time to hot-reload, unless we really mean it
    if (initialized.value && !forceReinitialize) {
      return;
    }

    // SettingsPort settings
    config.value.settingsPort.adapter = adapterName;

    const settingsAdapter = ((): SettingsPort => {
      switch (adapterName) {
        case 'env':
          return new EnvSettingsAdapter(import.meta.env);
        default:
          throw new InvalidAdapterError(`Invalid settings adapter: ${adapterName}`);
      }
    })();
    await settingsAdapter.init();

    // DataPort settings
    config.value.dataPort.adapter = settingsAdapter.getSetting(dataPortSetting);
    // ApiDataAdapter settings
    config.value.dataPort.apiConfig.uri = settingsAdapter.getSetting(apiDataSettings.uri);

    initialized.value = true;
  };

  return {
    config,
    init,
  };
});
