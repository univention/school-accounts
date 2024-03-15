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

### Gitlab Pipeline

#### integration-tests

The `integration-tests` job is a manual job that has to be started and succeed in order to merge any MR that contains changes
to the source code or the appcenter setup.
If you manually start a job by clicking on its name, instead of the play button, you can overwrite the jobs variables.
The following variables are important:

- TARGET_VERSION=5.0-6: The UCS version the tests should run under.
- KVM_SERVER=soft-test01.knut.univention.de: The KVM host to use for the tests.
- NO_HALT=UNSET: If the variable is set, the VMs are not automatically terminated.

If you abort the pipeline job or set the `NO_HALT` variable, make sure to clean up your VMs after.

They are named `build_ucsschool-user-management_$JOB_ID-{primary,backup1}`.
The IP addresses of the VMs can be extracted from the job log.

The job automatically determines which docker image to use for the app install. If the same pipeline builds a docker
image, that one is used. Otherwise, it defaults to the image specified in the compose file. You can overwrite which image
to use buy manually setting the `IMAGE_TAG` variable.

The job also installs the app with the appcenter files from the branch. Any changes made to compose, ini, etc., are
included automatically.

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

The UI can be accessed with "dev:univention" at http://user-management-proxy/univention/ucsschool/user-management/ui/

The API can be accessed at http://user-management-proxy/univention/ucsschool/user-management/bff/docs

Both UI and API react to code changes without the need to restart the environment.

Keycloak can be accessed with "admin:admin" at http://user-management-proxy/keycloak/admin/

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

THe e2e tests are designed to run against the environment that is created by the integration-test pipeline job.

If you want to manually run the tests, make sure to start the job with the `NO_HALT` variable set.
This way you have access to the setup after the job is done.

You can run the e2e tests for the backend with:

```shell
E2E_BASE_URL="https://backup1.school.test/univention/ucsschool/user-management" \
E2E_GUARDIAN_MANAGEMENT_URL="https://backup1.school.test/guardian/management" \
E2E_KELVIN_URL="primary.school.test" \
dev/dev_run.sh task pytest-e2e
```

Make sure that the domain names can be resolved. This can be achieved by entering the following into your `/etc/hosts`:

```text
IP_PRIMARY ucs-sso-ng.school.test ucs-sso.school.test primary.school.test
IP_BACKUP backup1.school.test
```

Make sure that the ssl certificate from the UCS domain is also downloaded and set in the .env file.

You can even use your local BFF as long as it is configured to use the Keycloak and Kelvin instances from the
integration test environment.

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
