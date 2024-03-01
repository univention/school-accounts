<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

# UCS@school User Management

This is the repository for the new UCS@school User Management Module.

## Development

### Prerequisites

To develop the UCS@school User Management Module you just need [docker](https://www.docker.com/).
Installation instructions for Ubuntu can be found [here](https://docs.docker.com/engine/install/ubuntu/).
You must have at least Docker version 25.

### Running commands in the development container

This repository provides a script, which allows you to run commands within a docker container,
that has all development tools preinstalled.

You can run any command `COMMAND` by executing

```shell
dev/dev_run.sh COMMAND
```

To run all pre-commit hooks for example, just execute

```shell
dev/dev_run.sh pre-commit run -a
```

### Use pre-commit

You can run pre-commit by executing the following command:

```shell
dev/dev_run.sh pre-commit run
```

Normally you use pre-commit by installing [pre-commit](https://pre-commit.com/) on your local machine
and running `pre-commit install` to install the pre-commit hook into the repository.
If you provide all the requirements, e.g. `python`, `nodejs`, `yarn`, etc. you can do so.

Alternatively you can use the following pre-commit hook, to execute pre-commit within docker,
so you do not need to install anything (other than docker) on your machine:

```shell
cat > .git/hooks/pre-commit << EOF
#!/bin/bash
dev/dev_run.sh pre-commit run
EOF
chmod +x .git/hooks/pre-commit
```

### Special tasks

The `dev_run` script provides some special tasks, which combine multiple or very long commands in one.
The available tasks are documented on the scripts help page, which can be accessed with:

```shell
dev/dev_run.sh --help
```

To run a task `TASK`, just execute:

```shell
dev/dev_run.sh task TASK
```

Some of those tasks are described in more detail here:

#### Start development server

To start the development server you have to execute the [dev_run.sh script](dev/dev_run.sh):

```shell
dev/dev_run.sh task dev-server
```

For Keycloak to work properly in the dev-server, you need to access the routes with the hostname
`user-management-proxy`. This means your browser needs to be able to resolve this hostname.
One way to achieve this, would be adapting your `/etc/hosts`:

```shell
echo "127.0.0.1    user-management-proxy" | sudo tee -a /etc/hosts
```

The UI can be accessed at http://user-management-proxy/univention/ucsschool/user-management/ui/

The API can be accessed at http://user-management-proxy/univention/ucsschool/user-management/bff/docs

Both UI and API react to code changes without the need to restart the environment.

Keycloak can be accessed at http://user-management-proxy/keycloak/admin/

#### Start live server for the manual

```shell
dev/dev_run.sh task sphinx
```

The manual can then be accessed at [http://localhost/docs/manual/](http://localhost/docs/manual/)

#### Cleanup the environment

Running the different services and jobs creates some artifacts:

- The `.cache` folder
- `node_modules` in [user-management-ui](user-management-ui)
- various docker containers, images and networks as part of the [docker compose setup](dev/docker-compose.yaml)

You can clean all of it by running:

```shell
dev/dev_run.sh task clean
```

#### Generating license annotations

License annotations can be created with the following command:

```shell
dev/dev_run.sh task reuse
```

If after this command the hook still fails, it means that the repo contains some files for which the tool does not know
how to automatically add licensing information.
In those cases you create a text file with the same name, but the suffix ``.license``
and the following content next to the file in question:

```text
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
```

#### Running e2e tests for the Backend

You can run the e2e tests for the backend with

```shell
dev/dev_run.sh task pytest-e2e
```

For these tests you have to have a proper environment setup. The current requirements are:

- The bff is running and available under the hostname `user-management-proxy`
- The BFF uses Kelvin for persistence and the Guardian for Authorization
- The UCS host contains one school named `school1`
- The school `school1` has a teacher named `teacher` and a student named `student`, both with password `univention`
- The teacher has the permission `create-user`, whereas the student does not.

Playwright traces and screenshots for failing tests of the latest test run are stored in `./cache/test-results`.

To inspect the trace of a test run you can run:

```shell
PLAYWRIGHT_BROWSERS_PATH=.cache/ms-playwright playwright show-trace .cache/test-results/$TEST_CASE_DIR/trace.zip
```

Please note that this only works if the `pytest-e2e` task was run at least once. Otherwise, necessary files
to run the trace might be missing.

You can interactively generate python code for playwright tests with the following command:

```shell
PLAYWRIGHT_BROWSERS_PATH=.cache/ms-playwright playwright codegen http://user-management-proxy/univention/ucsschool/user-management/bff/docs/
```

More information can be found [here](https://playwright.dev/python/docs/codegen-intro).

## App Center App

### Generating or updating files from templates

#### inst

The `inst` file is generated from a template, `templates/inst.tmpl`, by embedding
some scripts in it. To do so, either because the template has changed or because
the scripts have changed, you can run the following command:

```shell
cd appcenter-management
./scripts/generate-preinst
```
