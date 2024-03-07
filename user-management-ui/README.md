<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

# user-management-ui

This is the UI for the UCS@school `user-management` module.

## Development setup

See the top-level README for running the docker environment,
which is the preferred way to run the local development setup.

### Manually running the frontend through yarn

Copy and adjust the environment variables:

```bash
cd user-management-ui
cp .env.example .env.local
vi .env.local
```

Then start the frontend:

```bash
yarn dev
```

The frontend runs at [localhost:5173](http://localhost:5173/univention/ucsschool/user-management/ui/) by default.

### Linting

Pre-commit should handle linting for you:

```bash
../dev/dev_run.sh pre-commit run -a
```

But if you want to run linting manually, you can run the following three commands:

```bash
yarn lint
yarn type-check
yarn format
```

## Environment Variables

The `.env.example` files can be found in the following places:

* **docker:** `dev` directory in the top-level folder.
* **yarn:** `user-management-ui` directory.

The default settings in each of these files are sufficient to run docker or yarn, respectively.

Please note that for yarn, all variables must be prefixed with the `export` directive.

If you just want to do frontend development with yarn dev and without the backend,
you can use a local `.env.local` file:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__SETTINGS_PORT=env
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=in_memory
export VITE__USER_MANAGEMENT_UI__ADAPTER__AUTHENTICATION_PORT=in_memory
```

If you just want to do frontend development with yarn dev and without the backend,
you can use a local `.env.local` file:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__SETTINGS_PORT=env
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=in_memory
export VITE__USER_MANAGEMENT_UI__ADAPTER__AUTHENTICATION_PORT=in_memory
```

If you want to test specific adapters, these are the available settings:

### Settings Adapter

Get the settings from the `.env.local` file:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__SETTINGS_PORT=env
```

Get the settings from a URL:

```bash
export VITE__URL_SETTINGS_ADAPTER__URL=http://user-management-proxy/univention/ucsschool/user-management/bff/config/app
```

### Data Adapter

Use randomly-generated mock data:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=in_memory
```

Use an empty set of data:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=in_memory
export VITE__IN_MEMORY_DATA_ADAPTER__DB_DATA=emptyData
```

Use a test adapter that can mock errors with the in-memory adapter:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=test
export VITE__TEST_DATA_ADAPTER__SUB_ADAPTER=in_memory
export VITE__TEST_DATA_ADAPTER__ERROR_RESPONSES="fetchUsers:403 Forbidden|fetchUserColumns:404 Not Found"
export VITE__IN_MEMORY_DATA_ADAPTER__DB_DATA=testDefaultData
```

Use the BFF running in docker:

```bash
export VITE__API_DATA_ADAPTER__URI=http://user-management-proxy/univention/ucsschool/user-management/bff
```

### Authentication Adapter

Use a mock login:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__AUTHENTICATION_PORT=in_memory
export VITE__IN_MEMORY_AUTHENTICATION_ADAPTER__IS_AUTHENTICATED=1
export VITE__IN_MEMORY_AUTHENTICATION_ADAPTER__USERNAME=test-admin
```

Integrate with the Docker Keycloak instance:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__AUTHENTICATION_PORT=keycloak
export VITE__KEYCLOAK_AUTHENTICATION_ADAPTER__SSO_URI=http://user-management-proxy/keycloak
export VITE__KEYCLOAK_AUTHENTICATION_ADAPTER__REALM=ucs
export VITE__KEYCLOAK_AUTHENTICATION_ADAPTER__CLIENT_ID=ucsschool-user-management-ui
```
