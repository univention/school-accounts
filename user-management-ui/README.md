<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

# user-management-ui

This is the UI for the UCS@school `user-management` module.

## Development setup

See the top-level README for running the docker environment.

### End-to-end tests

There is a docker task for this:

```bash
../dev/dev_run.sh task playwright
```

However, the end-to-end tests can also be run locally by:

```bash
yarn test:e2e:setup  # only needed first time
yarn test:e2e
```

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

The `.env.example` file is located in the `dev` directory in the top-level folder.
The defaults are fine for the docker environment.

If you want to test specific adapters, these are the available settings:

### Settings Adapter

Get the settings from the `.env` file:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__SETTINGS_PORT=env
```

### Data Adapter

Use randomly-generated mock data:

```bash
export VITE__USER_MANAGEMENT_UI__ADAPTER__DATA_PORT=in_memory
```
