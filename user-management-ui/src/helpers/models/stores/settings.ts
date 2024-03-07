// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

interface UrlSettingsConfig {
  url: string;
}

interface SettingsPortConfig {
  adapter: string;
  urlConfig: UrlSettingsConfig;
}

interface ApiDataConfig {
  uri: string;
}

interface InMemoryDataAdapterConfig {
  dbData: string;
}

interface TestDataAdapterConfig {
  subAdapter: string;
  errorResponses: string;
}

interface DataPortConfig {
  adapter: string;
  apiConfig: ApiDataConfig;
  inMemoryConfig: InMemoryDataAdapterConfig;
  testConfig: TestDataAdapterConfig;
}

interface InMemoryAuthenticationConfig {
  username: string;
  isAuthenticated: boolean;
}

interface KeycloakAuthenticationConfig {
  ssoUri: string;
  realm: string;
  clientId: string;
}

interface AuthenticationPortConfig {
  adapter: string;
  inMemoryConfig: InMemoryAuthenticationConfig;
  keycloakConfig: KeycloakAuthenticationConfig;
}

interface InMemoryAuthenticationConfig {
  username: string;
  isAuthenticated: boolean;
}

interface KeycloakAuthenticationConfig {
  ssoUri: string;
  realm: string;
  clientId: string;
}

interface AuthenticationPortConfig {
  adapter: string;
  inMemoryConfig: InMemoryAuthenticationConfig;
  keycloakConfig: KeycloakAuthenticationConfig;
}

export interface SettingsConfig {
  settingsPort: SettingsPortConfig;
  dataPort: DataPortConfig;
  authenticationPort: AuthenticationPortConfig;
}
