// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {defineStore} from 'pinia';
import {ref} from 'vue';
import {
  EnvSettingsAdapter,
  InvalidAdapterError,
  type SettingsPort,
  UrlSettingsAdapter,
} from '@univention/univention-veb';
import {dataPortSetting} from '@/ports/data';
import {apiDataSettings} from '@/adapters/data';
import {type SettingsConfig} from '@/helpers/models/stores/settings';

export const useSettingsStore = defineStore('settings', () => {
  const initialized = ref(false);

  const config = ref<SettingsConfig>({
    settingsPort: {
      adapter: '',
      urlConfig: {
        url: '',
      },
    },
    dataPort: {
      adapter: '',
      apiConfig: {
        uri: '',
      },
    },
    authenticationPort: {
      adapter: '',
      inMemoryConfig: {
        username: '',
        isAuthenticated: false,
      },
      keycloakConfig: {
        ssoUri: '',
        realm: '',
        clientId: '',
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
    // UrlSettingsAdapter settings
    config.value.settingsPort.urlConfig.url = import.meta.env.VITE__URL_SETTINGS_ADAPTER__URL ?? '';

    const settingsAdapter = ((): SettingsPort => {
      switch (adapterName) {
        case 'env':
          return new EnvSettingsAdapter(import.meta.env);
        case 'url':
          return new UrlSettingsAdapter(config.value.settingsPort.urlConfig.url);
        default:
          throw new InvalidAdapterError(`Invalid settings adapter: ${adapterName}`);
      }
    })();
    await settingsAdapter.init();

    // DataPort settings
    config.value.dataPort.adapter = settingsAdapter.getSetting(dataPortSetting);
    // ApiDataAdapter settings
    config.value.dataPort.apiConfig.uri = settingsAdapter.getSetting(apiDataSettings.uri);

    // AuthorizationPort settings
    config.value.authenticationPort.adapter = settingsAdapter.getSetting('userManagementUi.adapter.authenticationPort');
    // InMemoryAuthorizationAdapter settings
    config.value.authenticationPort.inMemoryConfig.username = settingsAdapter.getSetting(
      'inMemoryAuthenticationAdapter.username'
    );
    config.value.authenticationPort.inMemoryConfig.isAuthenticated =
      settingsAdapter.getSetting('inMemoryAuthenticationAdapter.isAuthenticated') !== '0';
    // KeycloakAuthorizationAdapter settings
    config.value.authenticationPort.keycloakConfig.ssoUri = settingsAdapter.getSetting(
      'keycloakAuthenticationAdapter.ssoUri'
    );
    config.value.authenticationPort.keycloakConfig.realm = settingsAdapter.getSetting(
      'keycloakAuthenticationAdapter.realm'
    );
    config.value.authenticationPort.keycloakConfig.clientId = settingsAdapter.getSetting(
      'keycloakAuthenticationAdapter.clientId'
    );

    initialized.value = true;
  };

  return {
    config,
    init,
  };
});
