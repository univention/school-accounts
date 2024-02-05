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

The UI can be accessed at [http://localhost/univention/ucsschool/user-management/](http://localhost/univention/ucsschool/user-management/)

The API can be accessed at [http://localhost:8000/univention/ucsschool/user-management-bff/docs](http://localhost:8000/univention/ucsschool/user-management-bff/docs)

Both UI and API react to code changes without the need to restart the environment.

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
