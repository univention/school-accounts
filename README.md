<!--
SPDX-FileCopyrightText: 2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->

# UCS@school User Management

This is the repository for the new UCS@school User Management Module.
**Table of content**

[[TOC]]

- [UCS@school User Management](#ucsschool-user-management)
  - [Development](#development)
    - [Prerequisites](#prerequisites)
    - [Gitlab Pipeline](#gitlab-pipeline)
      - [Integration Tests](#integration-tests)
    - [Running commands in the development container](#running-commands-in-the-development-container)
    - [Use pre-commit](#use-pre-commit)
    - [Special tasks](#special-tasks)
      - [Start development server](#start-development-server)
      - [Reachable URLS](#reachable-urls)
      - [Generating Backend Translations](#generating-backend-translations)
      - [Start Cerbos server for development](#start-cerbos-server-for-development)
      - [Start live server for the manual](#start-live-server-for-the-manual)
      - [Cleanup the environment](#cleanup-the-environment)
      - [Generating license annotations](#generating-license-annotations)
      - [Running unit tests for the Backend](#running-unit-tests-for-the-backend)
      - [Running e2e tests for the Backend](#running-e2e-tests-for-the-backend)
      - [Running product tests](#running-product-tests)
  - [QA Checklist](#qa-checklist)
    - [Technical QA](#technical-qa)
    - [Functional QA](#functional-qa)
    - [Before merge](#before-merge)
    - [After Merge](#after-merge)
  - [App Center App](#app-center-app)
    - [Generating or updating files from templates](#generating-or-updating-files-from-templates)
      - [Inst script](#inst-script)
  - [Known Limitations and Issues](#known-limitations-and-issues)
    - [Limitations](#limitations)
    - [Issues](#issues)

## Development

### Prerequisites

To develop the UCS@school User Management Module you just need [docker](https://www.docker.com/).
Installation instructions for Ubuntu can be found [here](https://docs.docker.com/engine/install/ubuntu/).
You must have at least Docker version 25.

### Gitlab Pipeline

#### Integration Tests

The `integration-tests` job is a manual job that has to be started and succeed in order to merge any MR that contains changes
to the source code or the appcenter setup.
If you manually start a job by clicking on its name, instead of the play button, you can overwrite the jobs variables.
The following variables are important:

- TARGET_VERSION=5.2-6: The UCS version the tests should run under.
- KVM_SERVER=soft-test03.knut.univention.de: The KVM host to use for the tests.
- TERMINATE_INSTANCE=true: If the variable is set, the VMs are not automatically terminated.

If you abort the pipeline job or set the `TERMINATE_INSTANCE` variable, make sure to clean up your VMs after.

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
If you provide all the requirements, e.g. `python`, etc. you can do so.

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

Make sure that the `.env` is up-to-date: `cp dev/.env.example dev/.env`

For Keycloak to work properly in the dev-server, you need to access the routes with the hostname
`user-management-proxy`. This means your browser needs to be able to resolve this hostname.
One way to achieve this, would be adapting your `/etc/hosts`:

```shell
echo "127.0.0.1    user-management-proxy" | sudo tee -a /etc/hosts
```

#### Reachable URLS

The frontend page is served by the API at http://user-management-proxy/univention/ucsschool/user-management/ui/ .
Use "dev:univention" for the login at the frontend page.

The API can be accessed at http://user-management-proxy/univention/ucsschool/user-management/bff/docs

The API reacts to code changes without the need to restart the environment.

Keycloak can be accessed with "admin:admin" at http://user-management-proxy/keycloak/admin/

#### Generating Backend Translations

When adding a new string that will be returned to the frontend,
you need to mark it as translatable:

```python
from user_management_bff.lang import _

some_string = _("This needs to be translated")
```

In a Jinja template, use the `_` that `routes.render()` binds into the context:

```jinja
<title>{{ _("This needs to be translated") }}</title>
```

Extraction covers both: `pybabel extract` reads `*.py` and `templates/**.html`
through `user-management-bff/babel.cfg`, so a literal left untranslated in a
template fails the check the same way a Python one does.

If the msgid is only ever reached through a variable, extraction cannot see the
literal - mark it where it is defined and translate it at the point of use:

```python
from user_management_bff.lang import N_, _

_ROLE_LABELS = {"student": N_("Student")}
label = _(_ROLE_LABELS[role_id], lang=lang)
```

You can check existing translations and generate the compiled translations
either by running `pre-commit`, or via a separate task:

```shell
dev/dev_run.sh task translate
```

The script will tell you to fill in any translation strings it finds that are incomplete.
You can find the translation file in `user-management-bff/locales/de/LC_MESSAGES/ucsschool-user-mangement.po`.

**Note: Per default there is no `.mo` file present in the repository, therefore it is required to run the aforementioned task once, if localization is needed for development.**

Once all translation strings are resolved, you will receive a "Success!" message,
and it will compile the `.mo` translation files.

If you want to generate the files manually outside of docker,
you need `uv` (which supplies Babel from the `dev` dependency group) and gettext
(`msgmerge`, `msgattrib` and `msgfmt`):

```shell
sudo apt-get install -y gettext
```

#### Start Cerbos server for development

Currently as there is no adapter implemented the cerbos server can be started with

```shell
dev/dev_run.sh task cerbos-server
```

This might be integrated into the `dev-server` task if the adapter is rewritten.
If you want to check if a CEL expression is interpreted correctly you can run

```shell
docker exec -it ucsschool-user-management-ccerbos /cerbos repl
```

This will open a cerbos terminal in which you can type in the expressions, if you have the necessary data beforehand,
like `[1,2,3].exists(i, v, i==1 && v==2)`.

#### Start live server for the manual

```shell
dev/dev_run.sh task sphinx
```

The manual can then be accessed at [http://localhost/docs/manual/](http://localhost/docs/manual/)

#### Cleanup the environment

Running the different services and jobs creates some artifacts:

- The `.cache` folder
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
In those cases you add the path of the file to first block of the `REUSE.toml`, if for some reason it still does not work.
Add a text file with the same name and the suffix ``.license`` and the following content:

```text
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
```

#### Running unit tests for the Backend

You can run the unit tests for the backend with:

```shell
dev/dev_run.sh task pytest
```

It is also possible to pass additional arguments (limited to 7 arguments!) to pytest, e.g. to use the PDB on errors:

```shell
dev/dev_run.sh task pytest --pdb
```

#### Running e2e tests for the Backend

The e2e tests need a deployed environment. The integration-test pipeline job creates one -- start it with
the `TERMINATE_INSTANCE` variable set to anything but true to keep it afterwards -- and runs the tests
on that machine with `univention-app shell ucsschool-user-management python3 -m pytest -m "e2e"`.

Running them from your laptop against such an environment takes three preparations.

The domain names have to resolve. Add them to your `/etc/hosts`:

```text
IP_PRIMARY ucs-sso-ng.ucsschool.test ucs-sso.ucsschool.test primary.ucsschool.test
IP_BACKUP backup1.ucsschool.test
```

The UCS root CA has to be trusted.
Every instance mints its own,
so fetch it again whenever the environment is recreated --
an old one fails verification without saying that it is the wrong CA:

```shell
dev/scripts/fetch_ucs_ca.sh primary.ucsschool.test
```

Besides `dev/local/ucs-root-ca.crt` this writes `dev/local/ca-bundle.crt`,
the system roots and the UCS root concatenated.
`SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` replace the trust store rather than adding to it,
so pointing them at the UCS root alone would leave the process unable to verify PyPI.
Always use the bundle.

Cerbos has to be reachable. Nothing starts it for the tests, so leave it running in a second
terminal; it publishes 3592 and 3593 on the host:

```shell
dev/dev_run.sh task cerbos-server
```

Then run the tests **outside** the dev container, from the BFF's own virtualenv:

```shell
uv sync --inexact --project user-management-bff
cd user-management-bff
env SSL_CERT_FILE=../dev/local/ca-bundle.crt \
    REQUESTS_CA_BUNDLE=../dev/local/ca-bundle.crt \
    KELVIN_PERSISTENCE_ADAPTER__URL=primary.ucsschool.test \
    KELVIN_PERSISTENCE_ADAPTER__USERNAME=Administrator \
    KELVIN_PERSISTENCE_ADAPTER__PASSWORD=univention \
  uv run pytest -m "e2e" \
    --base_url "https://primary.ucsschool.test/univention/ucsschool/user-management" \
    --kelvin_url primary.ucsschool.test \
    --cerbos_url localhost:3593
```

The same tests also run inside the dev container, which needs two more things. A container never sees
the host's `/etc/hosts` and the UCS names are in no DNS zone it can reach, so add them to the
`extra_hosts` anchor in `dev/docker-compose.yaml`:

```yaml
    extra_hosts: &extra_hosts
      - git.knut.univention.de:${GITLAB_IP}
      - host.docker.internal:host-gateway
      - primary.ucsschool.test:IP_PRIMARY
      - ucs-sso-ng.ucsschool.test:IP_PRIMARY
      - ucs-sso.ucsschool.test:IP_PRIMARY
      - backup1.ucsschool.test:IP_BACKUP
```

Then uncomment these in `dev/.env`, so the processes in the container trust the UCS CA:

```text
REQUESTS_CA_BUNDLE=/src/dev/local/ca-bundle.crt
SSL_CERT_FILE=/src/dev/local/ca-bundle.crt
```

```shell
E2E_BASE_URL="https://primary.ucsschool.test/univention/ucsschool/user-management" \
E2E_CERBOS_URL="cerbos:3593" \
E2E_KELVIN_URL="primary.ucsschool.test" \
dev/dev_run.sh task pytest-e2e
```

Cerbos is reached at `cerbos:3593` over the compose network here, not on localhost.

The tests create users in the target environment and delete them again afterwards. The legal-guardian
tests additionally need the users the integration job imports from `dev/tests/import_users.csv`.

You can even use your local BFF as long as it is configured to use the Keycloak and Kelvin instances from the
integration test environment.

#### Running product tests

The product tests are using playwright. Their project, `dev/tests/product-tests/`, was removed in
`ff48630` and a replacement is planned -- until it lands, the commands below have nothing to run.

If you test against a fresh installation you need to add the same users as in `dev/tests/integration_tests.cfg`.

```shell
cd dev/tests/product-tests
uv sync --locked
# is needed if playwright is freshly installed in the project
# playwright install
CI_INTEGRATION=1 uv run pytest --base-url "https://$YOUR_TEST_INSTANCE"
# Or for debugging
#CI_INTEGRATION=1 PWDEBUG=1 uv run pytest --base-url "https://$YOUR_TEST_INSTANCE" --headed --browser firefox
```

## QA Checklist

This section is a collection of items which can be helpful for the QA process.
It is not meant to be obligatory -- pick and choose the ones that
are relevant for the issue at hand.

### Technical QA

Technical QA is focused on the code quality and basic runability of the code.
All Technical QA steps should also be performed by the implementer before handing over to QA.

- [ ] Code review on the merge request:
  - [ ] Changelogs are present (`README_UPDATE_*`-files and `docs/ucsschool-user-management-module/changelog.rst`)
  - [ ] Tests sufficiently cover the changed lines of code.
- [ ] Pipelines pass.
- [ ] App installation succeeds on a test VM.
- [ ] App update succeeds on a test VM.
- [ ] Basic smoke test:
  - [ ] If a service was changed (added, modified) the service is running after the installation and restarting works without problems. If it was removed, it must not be running anymore.
  - [ ] The app user-management are running.
  - [ ] Log in to the user-management ui as `alex.admin` and try to list and modify users.
  - [ ] New Cron jobs, listeners, etc. actually run.
  - [ ] Permissions are checked for new files (e.g., a script must be executable, right ownership of directories and created files in regard to data security).
  - [ ] New tests pass.

### Functional QA

Functional QA focuses on the user using the User Management UI.

- [ ] Post a QA plan on the gitlab issue of what will be tested:
  - [ ] Include a happy path and multiple non-happy path scenarios.
  - [ ] All software components that might be affected, not just the code that was changed.
  - [ ] Verify that examples in the documentation of the changed components still work.
  - [ ] Agree on QA plan with implementer.
- [ ] Manually run the QA plan
- [ ] Document all reproduction steps of the QA plan:
  - [ ] What commands were used to test?
  - [ ] What input values were used to test? Why were these values chosen?
  - [ ] Get creative and try to break the implementation
  - [ ] If possible, take screenshots before and afterward the fix.

### Before merge

 No merge without:

- [ ] Verify again that the integration tests pass in the pipeline.
- [ ] Gitlab integration tests pass.

### After Merge

- [ ] Gitlab integration tests pass after merge in main.
- [ ] Installation succeeds on a test VM.
- [ ] Smoke test installation: see section Technical QA.
- [ ] Gitlab issue is linked to release issue.

## App Center App

### Generating or updating files from templates

#### Inst script

The `inst` file is generated from a template, `templates/inst.tmpl`, by embedding
some scripts in it. To do so, either because the template has changed or because
the scripts have changed, you can run the following command:

```shell
cd appcenter-management
./scripts/generate-preinst
```

## Known Limitations and Issues

### Limitations

- roles can not be changed via front end at the moment
- `school_admin` is not properly supported by Kelvin
- Kelvin is currently not set up support multiple roles at different schools and will therefore produce false negatives when testing
- `FileAdapters` are not behaving identical to Kelvin (this is wanted)
- a session lives entirely in an encrypted cookie, which buys statelessness at three costs: an
  individual session cannot be revoked before it expires, a session is valid only on the UCS system
  that issued it (each host generates its own `session.secret`), and replacing that secret is the
  only way to end every app session at once — it does not sign anybody out, because the Keycloak
  session survives and carries the user straight back in

### Issues

- if the `user-management` is used **locally**, it can happen that `keycloak` crashes after inactivitiy --> the `docker-containers` need to be restarted afterwards
- error messages coming from Kelvin are currently not displayed properly `[{"loc":["body","name"],"msg":"Username must only contain numbers, letters and dots!","type":"value_error"}]`
- the `FileAdapters` are currently not setup to check the validity of user input e.g. escape-characters, special characters and username-collision
