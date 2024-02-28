// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';
import {defineStore} from 'pinia';
import {
  type AuthenticationPort,
  InMemoryAuthenticationAdapter,
  InvalidAdapterError,
  KeycloakAuthenticationAdapter,
} from '@univention/univention-veb';
import {type SettingsConfig} from '@/helpers/models/stores/settings';
import {type DataPort} from '@/ports/data';
import {ApiDataAdapter, InMemoryDataAdapter} from '@/adapters/data';

export const useAdapterStore = (config: SettingsConfig) => {
  return defineStore('adapter', () => {
    const authenticationAdapter: AuthenticationPort = (() => {
      const portSetting = config.authenticationPort.adapter;
      switch (portSetting) {
        case 'keycloak':
          return new KeycloakAuthenticationAdapter(
            config.authenticationPort.keycloakConfig.ssoUri,
            config.authenticationPort.keycloakConfig.realm,
            config.authenticationPort.keycloakConfig.clientId
          );
        case 'in_memory':
          return new InMemoryAuthenticationAdapter(
            config.authenticationPort.inMemoryConfig.username,
            config.authenticationPort.inMemoryConfig.isAuthenticated
          );
        default:
          throw new InvalidAdapterError(i18next.t('errors.invalidAuthenticationPort', {adapter: portSetting}));
      }
    })();

    const dataAdapter: DataPort = (() => {
      const portSetting = config.dataPort.adapter;
      switch (portSetting) {
        case 'api':
          return new ApiDataAdapter(config.dataPort.apiConfig.uri, authenticationAdapter);
        case 'in_memory':
          return new InMemoryDataAdapter(authenticationAdapter);
        default:
          throw new InvalidAdapterError(i18next.t('errors.invalidDataPort', {adapter: portSetting}));
      }
    })();

    return {
      authenticationAdapter,
      dataAdapter,
    };
  })();
};
