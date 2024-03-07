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
import {mockDbData} from '@/helpers/mocks/dbData';
import {type DataPort} from '@/ports/data';
import {ApiDataAdapter, InMemoryDataAdapter, TestDataAdapter} from '@/adapters/data';

const makeTestDataAdapter = (config: SettingsConfig, authenticationAdapter: AuthenticationPort): TestDataAdapter => {
  let subAdapter: DataPort | null = null;
  const subAdapterConfig = config.dataPort.testConfig.subAdapter;
  switch (subAdapterConfig) {
    case 'api':
      subAdapter = new ApiDataAdapter(config.dataPort.apiConfig.uri, authenticationAdapter);
      break;
    case 'in_memory':
      subAdapter = makeInMemoryDataAdapter(config);
      break;
    default:
      throw new InvalidAdapterError(`Invalid test sub-adapter: ${subAdapterConfig}`);
  }

  const errorResponses = new Map();
  // Example config:
  // fetchSchoolsSearch:403 Forbidden|fetchUsers:404 Not Found
  const errRespConfig = config.dataPort.testConfig.errorResponses.split('|');
  errRespConfig.forEach(errResp => {
    if (errResp !== '') {
      const errRespVals = errResp.split(':');
      if (errRespVals.length == 2) {
        errorResponses.set(errRespVals[0], errRespVals[1]);
      }
    }
  });

  return new TestDataAdapter(subAdapter, errorResponses);
};

const makeInMemoryDataAdapter = (config: SettingsConfig): InMemoryDataAdapter => {
  const dbDataConfig = config.dataPort.inMemoryConfig.dbData;
  const dbData = mockDbData[dbDataConfig];
  return new InMemoryDataAdapter(dbData);
};

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
          return makeInMemoryDataAdapter(config);
        case 'test':
          return makeTestDataAdapter(config, authenticationAdapter);
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
