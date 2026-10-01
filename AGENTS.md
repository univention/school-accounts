<!--
SPDX-FileCopyrightText: 2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->

# Repository Guidelines

## Project Overview

School Accounts: a single deployable app (`ucsschool-accounts`) combining a
Python/FastAPI backend-for-frontend with a server-rendered HTMX UI, plus the UCS "App Center"
packaging that installs it into a UCS@school domain. There is **no separate frontend project** —
the old Vue SPA (`user-management-ui/`) was removed; see
[dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) for the full port history and design
rationale. That document is the authoritative deep-dive; this file is the operational summary —
read the former before making any non-trivial UI/architecture change.

Top-level areas:

- [ucsschool-accounts/](ucsschool-accounts/) — the application: FastAPI + Jinja2 + htmx. Nearly
  all day-to-day work happens here.
- [appcenter-management/](appcenter-management/) — UCS App Center install/config scripts, Docker
  Compose templates, and Cerbos authorization policies (`.yaml` resource/derived-role policies under
  `appcenter-management/files/policies/`, registered in LDAP on join as a Guardian policy bundle for
  a Cerbos-hosting listener to pick up — see `appcenter-management/inst`/`templates/preinst.tmpl`).
  Independent from the app's own permission adapter (§ Architecture) — only touch this when changing
  how the app is *installed* or how Cerbos policies are evaluated for this app, not for
  UI/business-logic changes.
- [docs/ucsschool-accounts/](docs/ucsschool-accounts/) — the published
  Sphinx user manual (installation, configuration, troubleshooting, changelog). User-facing, built
  in CI (`docs:*` jobs from the `sphinx-docs` CI component); not developer documentation.
- [dev/](dev/) — local dev environment (Docker Compose, Keycloak provisioning, fixture data,
  scripts, integration-test config). See § Development Environment.

## Repository Structure (`ucsschool-accounts/`)

```text
ucsschool_accounts/
  main.py                   FastAPI app, middleware, global exception -> HTML handlers
  routes.py                 all UI routes (thin handlers), render() helper
  business_logic.py         domain rules + permission checks; no I/O of its own, calls only ports
  presentation.py           shapes business_logic results into template view models
  ports.py                  abstract port interfaces (persistence, auth, permissions)
  adapter_registry.py       binds ports -> concrete adapter classes via env vars; port_dep() DI helper
  adapters/                 concrete adapters: Kelvin/File persistence, Guardian/File permissions,
                             Keycloak cookie-session auth + dev/test auth doubles
  session_cookie.py          encrypts/decrypts the self-contained session cookie (Fernet)
  session_middleware.py      puts a refreshed session cookie onto the outgoing response
  models.py                 domain models (User, School, SessionRecord, Permission, UsersGetRequest, ...)
  constants.py               env-var-driven config: frontend prefix, auth paths, session-secret
                             loading, supported languages
  correlation_id.py          request correlation-id ContextVar, read by the logging middleware
  logging.py                 loguru configuration
  errors.py                 domain exceptions (PermissionsError, ObjectNotFoundError, ...)
  lang.py                   gettext-based i18n; _() translation helper, N_() extraction marker
  templates/
    base.html                root layout: <head>, vendored asset tags, {% block body %}
    pages/                    full-page templates (user_list, message)
    fragments/                htmx partials (user_table, user_filters, school_options, group_options, toast)
    macros/                   layout.py-style Jinja macros: page_header/toast, cell() cell-kind dispatch
  static/vendor/             vendored htmx, Alpine.js, Univention design-system (CSS/JS/web components)
locales/                    gettext catalogs (de/LC_MESSAGES/...) — sibling of ucsschool_accounts/, not nested under it
keycloak_provisioning/       separate Typer CLI: seeds Keycloak realms/clients/users for dev/test only;
                             unrelated to the adapters above, not for production use
tests/
  adapters/                  adapter-level tests (one file per adapter)
  e2e/                       Playwright-driven backend e2e tests, marked `e2e`, require a live env
  frontend/                  browser-driven UI tests, marked `frontend`, require a running deployment
  keycloak_provisioning/     tests for the provisioning CLI
  data/                      small, test-owned JSON fixtures (mirror of dev/data/*.json shape)
  test_routes.py             route/HTTP-level tests: TestClient + dependency_overrides, assert on
                             rendered HTML, hx-* attributes, and response headers
  test_adapter_registry.py, test_business_logic.py, test_presentation.py, test_lang.py, ...
```

## Architecture and Dependency Boundaries

Hexagonal (ports-and-adapters), one-way dependency flow:

```text
routes.py  →  business_logic.py  →  presentation.py  →  Jinja2 template
   │                  │
   └─ Depends(port_dep(SomePort)) resolves to a concrete adapter, chosen purely by env var
```

- **routes.py**: thin FastAPI handlers only. Auth via `Depends(current_actor)`, data access via
  `Depends(port_dep(SomePort))`. No permission logic of its own lives here. There are currently no
  mutating routes at all (see § Forms, Validation, and Mutations).
- **Group lookups come in two sizes, and neither is optional**: `get_school_classes(school)` /
  `get_work_groups(school)` return the whole school and back the filter sidebar, which has to list
  everything; `get_*_by_name(school, names)` return exactly the named groups and back the check
  that a selected group still exists when its listing comes back empty (`_Listing.holds` in
  `routes.py`). Use the by-name form for a question about specific groups — the whole-school
  lookup ships every group of the school, so a big school makes it large and slow to answer a
  question about one. The results table shows no groups at all. Both forms are per-port abstract methods with a contract test matrix over every
  implementation (`tests/adapters/test_school_classes.py`, `test_work_groups.py`); an unknown name
  is skipped, and an empty `names` costs no I/O at all.
- **Per-request read cache**: the schools / school-classes / work-groups deps are wrapped in the
  `RequestCached*Adapter` decorators from `adapters/request_cache.py` (see the `cached_*_persistence`
  dependencies in `routes.py`). A handler asks for the same school more than once — the sidebar and
  the selected-group check overlap — and FastAPI resolves a dependency once per request, which is what scopes the
  cache. The group caches are keyed per group, and the whole-school read fills them, so a
  by-name lookup for a school the sidebar already loaded costs nothing. Keep new read-only lookups
  going through those deps rather than the raw `port_dep(...)`, and don't widen the cache beyond one
  request: there is no invalidation channel for a group renamed in Kelvin.
- **business_logic.py**: the *only* place permission checks and domain rules live. Never touches
  `Request`/`Response`/Jinja; only calls ports. Read paths must filter out anything the actor lacks
  permission on (existing pattern in `get_school_classes`, `get_work_groups`, which keep only items
  carrying `Permission.use_as_filter`).
- **presentation.py**: pure functions turning `business_logic` results into template-ready
  dataclasses — `Option`/`OptionGroup` (filter dropdowns) and `Column`/`Cell`/`Row`/`UserListView`
  (the results table). No I/O, no permission decisions of its own — only reshaping what
  `business_logic` already decided (see § Templates and UI Fragments for the `Cell.visible`/`kind`
  pattern).
- **ports.py / adapter_registry.py**: adding a new backing system means adding a port method (if
  needed), then a new adapter class implementing it, then wiring it into `AdapterSelection` in
  `adapter_registry.py` — never branch on environment/deployment inside `business_logic.py` or
  `routes.py` itself.
- **No database anywhere.** "Persistence" is either an external service (Kelvin REST API for
  users/schools/classes/work-groups, Cerbos for permissions, Keycloak for auth) or, in dev/test, a
  flat JSON file (`File*Adapter`) that is fully re-read and rewritten on every mutation — fine for
  single-developer use, not a model to extend for concurrency.
- **Permissions are Cerbos-native**: `CerbosPermissionsAdapter` (`adapters/permissions.py`) talks
  directly to Cerbos's own gRPC API (`cerbos.sdk.grpc.client.AsyncCerbosClient`), mapping domain
  `User`/`Target` objects to Cerbos `Principal`/`Resource` (Protobuf messages, built via
  `google.protobuf.struct_pb2.Struct` for attribute maps) per the policies in
  `appcenter-management/files/policies/` — the resource-kind/role strings in that YAML are
  authoritative. `compose.jinja` hardcodes `CERBOS_PERMISSIONS_ADAPTER__CERBOS_TARGET: 'cerbos:3593'`,
  a bare `host:port` gRPC target rather than a URL, with no UCR variable/App Center setting behind
  it and no OAuth2 step.
- **Cerbos policies are additive**: every rule in `appcenter-management/files/policies/` is
  `EFFECT_ALLOW`. Never add an `EFFECT_DENY` rule. A restriction is an extra condition on each
  grant it limits, so a rule granting reads and `write-password` over the same set gets split in
  two when only the write side is restricted. Phrase the condition positively, as the allow list
  of values that pass rather than a negated probe for the one to block, so an unforeseen value
  fails the check instead of slipping through. The cost is that a restriction is restated on
  every grant it applies to, and each copy needs its own test — dropping one must fail
  `cerbos compile`.
- **Who may reset whose password is data, not rules**: one `write-password` rule, driven by the
  `password_reset_matrix` table in `files/policies/constants/password_reset_constants.yaml`
  (resource role → principal role → the relationships required between those two role entries).
  Adding a role driven route is an edit to that table. Inside the policies use Cerbos's words,
  `resource` and `principal`, not the app's `Target`/`actor` — the adapter is where the two
  vocabularies meet. A reset needs a cell for *every* role its resource holds
  (`variables.principal_may_reset_every_resource_role`) and one pair of role entries that
  satisfies its relationships (`variables.matrix_binds_a_role_pair`). Authority is per role name
  and context free; the binding supplies the context. So an absent role protects its holder's
  password from everyone (`school_admin`, and anything the directory service invents), and a role
  only a `school_admin` may reset puts its holder out of a teacher's reach even when they are
  also a student in that teacher's class. `legal_guardian` is a key because every guardian holds
  it, so leaving it out would protect every parent's password from their own `school_admin` too;
  keying it to `school_admin` alone is deliberate, and puts a pupil who is a guardian out of
  their teacher's reach. Relationship *names* are data, their implementations are the
  `relation == "…" && <expr>` chain — a relationship is a predicate over the pair of entries, and
  a CEL variable takes no parameters. Keep that chain lazy: a `{name: <expr>}[relation]` lookup
  builds the map eagerly and errors on principals lacking an optional attribute. Authority is
  `all()` over the resource's roles and the binding is `exists()`; swapping either breaks a
  pinned test.
- Which adapter backs each port is selected only via `UCSSCHOOL_ACCOUNTS__ADAPTER__*` env vars
  (`dev/.env.example` documents all of them); never gate adapter choice on anything else.

## Logging, Correlation IDs, and Sessions

- **Logging**: use loguru's structured form — `logger.<level>(message, key=value, ...)`, never
  f-strings/`.format()`. Log from `business_logic.py`, `presentation.py` and the adapters.
  `routes.py` logs only the filter-state decisions it makes itself and no other layer sees (a
  school the actor cannot filter by, a dropped group filter); anything a port or a domain rule
  decides belongs where that decision is made — a rejected CSRF token is logged by the
  authentication adapter, not by the dependency that raises. Levels follow
  [ADR 0005](https://git.knut.univention.de/univention/dev/decision-records/-/blob/main/dev/0005-log-levels.md):
  `debug` for technical context, `info` for a completed business event, `warning` only for a
  handled surprise (never for wrong user input) and it must say how to avoid it next time,
  `error` for what the service cannot handle but survives, `critical` for what stops every
  future request, stating why.
- **Correlation ID** (`correlation_id.py`): a `ContextVar` set once per request by `main.py`'s
  middleware (from the `X-Request-ID` header or a generated UUID), automatically attached to
  every loguru call in that request and echoed back as a response header. This is transparent
  for normal request-scoped code — no action needed — but it will **not** propagate into a
  manually spawned background task/thread that outlives the request's async context.
- **Sessions are three distinct concepts — don't conflate them**: Starlette's
  `SessionMiddleware` cookie holds only transient OAuth `state`/PKCE `code_verifier` during
  login; the authenticated session is the whole `SessionRecord`, encrypted into a second cookie
  by `session_cookie.py` and stored nowhere on the server; and `adapters/base.py`'s per-request
  `self.kelvin_session` is unrelated — just the HTTP session used for a single Kelvin API call. A
  new adapter author searching for "session" should be sure they're looking at the right one.
- **The authenticated session is stateless, deliberately.** There is no session store and no
  `SessionStorePort` — every field travels in the cookie, so any gunicorn worker serves any
  request and sessions survive a restart/app update as long as `session.secret` does. What that
  costs is listed in `docs/.../configuration.rst`. Two traps when editing: bump
  `session_cookie.COOKIE_VERSION` when `SessionRecord` changes shape, and write a refreshed
  cookie through `request.state.pending_session` — `session_middleware.py` says why nothing
  simpler works.
- **The UI's OIDC client is confidential, its secret belongs to the domain, and the file that
  holds it is per host.** The preinst generates `conf/client.secret` before the container
  exists, because `entrypoint.d/10-copy-secrets.sh` copies it into `/run/secrets` at boot and
  the join script only runs afterwards. The client itself lives in the shared `ucs` realm, so
  the join script asks Keycloak for the registered secret first and, when there is one, writes
  it into the file and restarts the container — the entrypoint copied the generated value at
  boot and would otherwise keep serving it. Registering the generated value unconditionally
  would lock out every other host that had already registered its own. Only a first
  installation in the domain gets to keep what the preinst generated.
- **`revoke.refresh.token: "false"` in the shipped UI client JSON is load-bearing.** Nothing
  serializes the refresh, so two htmx requests that cross `expires_at` at the same time both
  present the same refresh token; with Keycloak's rotation enabled one of them would be rejected
  and force a spurious re-login. Turning rotation on needs refreshes coordinated across workers
  first — the shared state this design does without.

## HTMX Request and Rendering Model

- **Every response is HTML.** `main.py` sets `default_response_class=HTMLResponse` and
  `openapi_url=None` — there is no JSON API surface. Do not add JSON endpoints; extend the HTML/htmx
  pattern instead.
- **A route may answer an htmx request with only the fragment it swaps, keyed on `HX-Target`.**
  `GET /users` does:
  the filter form targets `#results-region`,
  and for that request the route renders `fragments/results_region.html`
  instead of `pages/user_list.html` (`_Listing.results_only` in `routes.py`),
  skipping the group control the swap would discard —
  2.9 s of a 3.3 s request on a school with 501 groups.
  What keeps such a branch safe:
  - Every other request gets the full page.
    A pushed URL must reproduce on a reload or a shared link
    what the click showed, so filtered URLs stay bookmarkable.
    The route pushes it with `HX-Push-Url`;
    an `hx-push-url` attribute would also push after an error toast.
  - Key on `HX-Target`, not on `HX-Request` alone.
    A history restore after a cache miss sends `HX-Request: true` as well
    (`historyRestoreAsHxRequest` is on by default in htmx 2) but names no target,
    and needs the whole page.
  - Render the fragment the page itself includes, so both responses show the same region,
    and keep `hx-select` on the trigger:
    `GET /users` still answers the filter form with the full page while no school is chosen.
  - Send `Vary: HX-Request, HX-Target`, as `GET /users` does.
    One URL has two bodies, and a browser going back to a pushed URL
    can otherwise show the cached fragment as the whole page.
- The global error/redirect handling (`main.py:_html_error`, `not_authenticated_exception_handler`)
  branches on `HX-Request` too,
  answering an htmx request with `HX-Redirect` or a toast instead of a page.
- **The UI is read-only apart from the password reset and the header's logout** (first-release
  scope). When a mutating endpoint is added, a success response should return
  `Response(status_code=200, headers={"HX-Redirect": ...})` (which htmx follows client-side) rather
  than JSON or a raw redirect status, consistent with how `NotAuthenticatedError` already uses
  `HX-Redirect` below.
- **The logout button is a plain `<form method="post">`, not htmx** (`macros/layout.html`). The
  route answers 303 into Keycloak's cross-origin `end_session_endpoint`, which htmx cannot follow;
  it needs a real browser navigation. `u-button type="submit"` submits it because the element is
  form-associated.
- **Auth failures** also render as HTML: `NotAuthenticatedError` → `HX-Redirect` to `/auth/login` for
  htmx requests, a normal 303 otherwise; any `PermissionsError` → a toast fragment retargeted at
  `#toast-region` (`HX-Retarget`/`HX-Reswap`) for htmx requests, a full `pages/message.html`
  otherwise. Reuse these existing exception types/handlers for new failure cases instead of building
  bespoke error responses.

## Templates and UI Fragments

- `templates/pages/*` — full pages, always extend `base.html` via its `{% block body %}`.
- `templates/fragments/*` — htmx partials, targeted by `hx-target`/`hx-select` from a page or another
  fragment. Cascading filter endpoints (`/users/schools`, `/users/groups`, and the school→group
  cascade `/users/filters`) are fragment-only routes, never used for full-page loads.
- `templates/macros/*` — shared rendering logic: `layout.html` (`page_header()`, `toast()` chrome),
  `user_table.html` (`cell(cell)` — the cell-kind dispatch described below).
- **Cell visibility/kind pattern** (`presentation.build_user_list`): each table cell gets a `visible`
  flag computed from the actor's per-attribute permission (`_text_cell`/`_list_cell`/`_boolean_cell`
  helpers) plus a `kind` (`text | list | boolean`). `macros/user_table.html`'s `cell(cell)` macro is a
  flat dispatch on that value — a field the actor can't read is never rendered. **When adding a new
  column, compute its visibility/kind in `presentation.py`, don't branch on raw permissions in the
  template.** This is what makes it structurally impossible to leak an attribute the actor isn't
  allowed to see.
- New page → add under `pages/`, extend `base.html`, add a route in `routes.py` calling
  `business_logic` + `presentation`, and register it the same way as `/users`.
- New reusable fragment / htmx-only endpoint → add under `fragments/`, give it its own route (see
  `users_school_options` and `users_group_options` for the pattern), and keep any in-memory filtering
  it does consistent with the existing `q`-filtering stopgap noted in `routes.py` (a comment there
  flags this as filtering every option per keystroke — don't silently extend that cost further
  without checking the comment).
- Error/empty/loading states: `fragments/toast.html` (`#toast-region`, one `<u-toast-item>` per
  message) and `pages/message.html` are the established shells — reuse them rather than inventing new
  ones. There's no dedicated loading-indicator convention yet beyond what the design-system's custom
  elements provide.

## Forms, Validation, and Mutations

The UI is read-only apart from the password reset and the header's logout form (this is the
first-release scope; the previous user detail/edit view and its form handling were removed in the
`drop unused code` refactor). Permission errors from `business_logic` are still raised as
`PermissionsError` and turned into a 403 toast by the global handler — don't catch/render these
manually in route handlers.

Logout needs no CSRF token: the route is POST-only and the session cookie is `SameSite=lax`, which
already keeps a cross-site POST from carrying it.

## JavaScript and Asset Boundaries

- **Alpine.js is vendored and loaded on every page but currently unused anywhere** (no `x-data` in
  any template). All client-side interactivity today comes from the Univention design-system's
  custom elements (`<u-combobox>`, `<u-multiselect>`, `<u-table>`, ...) firing DOM events (`u-search`,
  `u-change`) that htmx listens for via `hx-trigger` — there is no repo-authored JavaScript file.
  Prefer this event-driven htmx pattern; reach for Alpine only for behavior that genuinely can't be
  expressed as an htmx-observable DOM event, and don't add a new JS bundling/build step without
  discussing it first (none exists today).
- htmx, Alpine, and the design-system bundle are **vendored** under
  `ucsschool_accounts/static/vendor/` (not installed via pip/npm). See § Generated and Sensitive
  Files before touching them.
- The design-system CSS is loaded as a render-blocking `<link>` deliberately (commit `66a610f`, fixed
  a flash-of-unstyled-content bug) — don't revert to runtime style injection.

## Development Environment

Everything runs through the Docker-based dev container; there is no supported bare-metal setup
beyond having `docker` (>= 25) installed.

- `dev/dev_run.sh COMMAND` — runs `COMMAND` inside the dev container (equivalent to a docker compose
  `run`).
- `dev/dev_run.sh task TASK` — runs a predefined task; run `dev/dev_run.sh --help` for the current
  list. Key tasks:
  - `dev-server` — starts the FastAPI dev server + Keycloak (via `dev/docker-compose.yaml`); code
    changes are picked up live. Requires `ucsschool-accounts-proxy` to resolve (add it to `/etc/hosts`).
    UI: `http://ucsschool-accounts-proxy/univention/ucsschool/ucsschool-accounts/ui/`. API docs:
    `.../bff/docs`. Keycloak admin: `.../keycloak/admin/` (`admin:admin`).
  - `pytest` — unit/integration tests (excludes the `e2e`- and `frontend`-marked tests); forwards
    any further arguments to pytest, e.g. `dev/dev_run.sh task pytest --pdb`.
  - `pytest-e2e` — Playwright-backed backend e2e tests against a real deployed environment; requires
    `E2E_BASE_URL`, `E2E_CERBOS_URL`, `E2E_KELVIN_URL` and resolvable domain names (see
    [README.md](README.md#running-e2e-tests-for-the-backend)). Not runnable standalone locally.
  - `pytest-frontend` — Playwright-driven UI tests against a running deployment; defaults to the
    `dev-server` stack, so start that first. `FRONTEND_BASE_URL` points it at an installed system,
    where `--kelvin_url` additionally makes the suite seed its own test data
    (see [README.md](README.md#running-frontend-tests)).
  - `pytest-frontend-headed` — the same run in a visible browser window, slowed down and with the
    host's X server wired into the container; needs `DISPLAY`. Use it to watch a failing
    interaction, with `PWDEBUG=1` for the Playwright inspector.
  - `translate` — verifies and (re)compiles gettext translations; must be run at least once locally
    since `.mo` files are git-ignored (see § Documentation and Changelog Requirements).
  - `cerbos-server` — starts a local Cerbos server for manually testing policies from
    `appcenter-management/files/policies/`, or for running `CerbosPermissionsAdapter` against a real
    PDP (e.g. `tests/e2e/test_cerbos_permissions_adapter.py`); not wired into `dev-server`/
    `prod-server` yet, so start it separately when exercising permission checks locally.
  - `cerbos-compile` — lints/tests the Cerbos policies (`cerbos compile`); also in pre-commit as a manual stage.
  - `reuse` — generates SPDX license headers/`.license` sidecar files.
  - `sphinx` — live server for the manual at `http://localhost/docs/manual/`.
  - `prod-server` — starts the production Docker image (built image, not the live-reload dev server).
  - `clean` — removes `.cache/`, build artifacts, and the dev docker containers/images.
- `dev/dev_run.sh pre-commit run [-a]` — runs the pre-commit suite (see § Testing and Validation).
- `dev/.env` is created from `dev/.env.example` on first run and is **git-ignored** — treat any
  `dev/.env*` file other than `.env.example` as local/untracked, never edit or commit it.
- The frontend tests (`ucsschool-accounts/tests/frontend/`) need a deployment to drive, so they are
  excluded from the normal backend test loop by the `frontend` marker. CI stands up their stack in
  the `accounts-frontend-test` job (Keycloak service container + the app on the File adapters, started
  from `dev/.env.example` in the job itself); locally the `dev-server` stack is that deployment.
  The manual `integration-tests` job also runs them, seeded through Kelvin, against the UCS VM it
  installs the app on (`dev/tests/run_frontend_tests.sh`, from `integration_tests.cfg`).

## Common Commands

All commands below are `dev/dev_run.sh` invocations (run from the repo root) unless noted; they wrap
docker compose so no local Python/Node install is required.

| Goal | Command |
| --- | --- |
| Run backend unit/integration tests | `dev/dev_run.sh task pytest` |
| Run a single test file/case | `dev/dev_run.sh task pytest ucsschool-accounts/tests/test_routes.py::test_users_search_renders_results` |
| Run backend e2e tests | see § Development Environment — requires a live `E2E_*` environment |
| Run the frontend tests | `dev/dev_run.sh task dev-server --detach --wait`, then `dev/dev_run.sh task pytest-frontend` |
| Watch a frontend test in a real browser | `dev/dev_run.sh task pytest-frontend-headed` |
| Run all pre-commit hooks (lint/format/type-check/license/translation) | `dev/dev_run.sh pre-commit run -a` |
| Run pre-commit only on staged files | `dev/dev_run.sh pre-commit run` |
| Precise type check (basedpyright, matches CI) | `uvx prek run --hook-stage manual basedpyright-accounts-container-baseline --all-files` |
| Start the dev server | `dev/dev_run.sh task dev-server` |
| Start a local Cerbos server (manual policy/adapter testing) | `dev/dev_run.sh task cerbos-server` |
| Lint/test the Cerbos policies (`cerbos compile`) | `dev/dev_run.sh task cerbos-compile` |
| Regenerate/verify translations | `dev/dev_run.sh task translate` |
| Generate license headers | `dev/dev_run.sh task reuse` |
| Serve the Sphinx manual locally | `dev/dev_run.sh task sphinx` |
| Clean dev artifacts/containers | `dev/dev_run.sh task clean` |
| Regenerate the App Center `inst` script | `cd appcenter-management && ./scripts/generate-preinst` |

CI (`.gitlab-ci/gitlab-ci.yml`) runs the equivalent of `pytest -m "not e2e and not frontend"` with **coverage gated via
the `ACCOUNTS_COVERAGE_LIMIT` CI variable (currently `"100"`, i.e. 100%)** over `ucsschool_accounts` +
`keycloak_provisioning` (excluding `main.py` and `constants.py` — see
`[tool.coverage.run] omit` in `pyproject.toml`). New code outside those three omitted files must be
fully covered or CI fails.

## Coding Conventions

Enforced by tooling (pre-commit, see `.pre-commit-config.yaml`) — treat these as required, not
optional:

- **black** (line length 105, target py311) and **ruff** (`E, F, I, B`, `B008`/`B904` ignored,
  `--fix`) — both configured in `ucsschool-accounts/pyproject.toml`.
- **basedpyright** on the package (config: `ucsschool-accounts/pyrightconfig.json`) with a committed
  baseline (`basedpyright-baseline.json`) suppressing pre-existing findings — only *new*
  diagnostics fail the pre-commit hook/CI job. The default `basedpyright-*-native-baseline` hooks run
  against the host's `uv`-managed venv; for a precise type check that matches CI exactly, run the
  containerized hook instead: `uvx prek run --hook-stage manual basedpyright-accounts-container-baseline
  --all-files`. These container hooks are `stages: [manual]`, so `pre-commit run -a`
  alone skips them — invoke them explicitly when you want a trustworthy type-check result.
- **bandit** on everything except `tests/` and `appcenter-management/scripts/test_*`.
- **reuse** — every source file needs an SPDX header or a matching `.license` sidecar file (see the
  many `*.license` files already in the tree for the pattern).
- **pymarkdown** on Markdown files (arbitrary line length, duplicate headings, bare URLs, and
  missing-top-heading rules are disabled; other rules apply).
- Commit messages: **Conventional Commits, strictly enforced** (`conventional-pre-commit --strict`),
  plus a required issue reference trailer (`Issue <project>#<number>` or `Bug #<number>`) checked by
  the local `issue-reference` hook.
- User-facing strings must be wrapped in `_()` from `ucsschool_accounts.lang` (see
  `from ucsschool_accounts.lang import _`) so they flow into the translation catalog — see next
  section for the follow-up step this requires. This applies to Jinja templates too: extraction
  runs `pybabel extract` over `*.py` **and** `templates/**.html` via `ucsschool-accounts/babel.cfg`,
  so an untranslated `{{ _("...") }}` fails the check exactly like a Python one.
- A msgid that is only ever reached through a variable (a role label looked up by id, say) is
  invisible to extraction. Mark the literal with `N_()` where it is defined — see `_ROLE_LABELS` in
  `presentation.py` — and call `_()` on the looked-up value.
- Call `.format()` on the **result** of `_()`, never on the msgid inside the call: interpolating
  first means the lookup key is the interpolated string, which never matches a catalog entry and
  silently stays English.

**Type-only imports go under `if TYPE_CHECKING:`, paired with `from __future__ import
annotations`** — not gated by a specific tool, but treat as required, since getting it wrong is a
real runtime bug rather than a lint nit. Add `from __future__ import annotations` at the top of
every new or touched module (as most `tests/` files and `adapters/permissions.py` already do), so
annotations are deferred/stringified automatically. An import used exclusively inside type
annotations — never instantiated/called, never a base class, never in an `isinstance`/`except`
clause, and never the right-hand side of a module-level `X: TypeAlias = ...` assignment — belongs
in the `if TYPE_CHECKING:` block, not as a top-level import; with the future import present, none
of these annotations need quoting anymore (no `-> "SomeType"`).

- Some older files still lack `from __future__ import annotations`, in which case any annotation
  referencing a `TYPE_CHECKING`-only name must be a quoted string, e.g. `-> "SomeType"` — bring a
  file onto the future-import form when you touch it rather than adding more quoting to it.
  `adapters/permissions.py` used to be one of these, worked around this way because
  `port_loader`'s `EnvSettingsProvider` read `dataclasses.Field.type` raw and broke under deferred
  annotations (`univention/dev/libraries/port-loader#3`) — fixed upstream, so this is no longer a
  reason to avoid the future import.
- Don't move a name that's genuinely evaluated at runtime — e.g. the RHS of a module-level
  `TypeAlias`, a decorator, a base class, an `except`/`isinstance` target, or anything actually
  constructed/called in a method body — into `TYPE_CHECKING`, and don't drop its quotes either:
  `from __future__ import annotations` only defers annotation positions (`def`/variable
  annotations), not arbitrary expressions, so a self-referential `TypeAlias` like
  `adapters/permissions.py`'s `_StructValue: TypeAlias = ... | Mapping[str, "_StructValue"]` still
  needs its own quoting regardless of the future import. Moving such a name into `TYPE_CHECKING` or
  unquoting it raises `NameError` at import/definition time, not just a type-checker complaint.

Non-mandatory but consistently observed in current code: dataclasses (not classes) for view
models/data bundles in `presentation.py`; ports/adapters named `<Noun>Port` / `<Adapter><Noun>Adapter`;
docstrings explaining *why* a design choice was made (e.g. `authentication.py` module docstring on why
no access token is stored) rather than restating what the code does.

## Testing and Validation

- **Route/HTTP-level tests** (`tests/test_routes.py`): `TestClient` + `app.dependency_overrides` on
  the module-level `port_dep(...)` callables (e.g. `auth_port`). Assertions check rendered HTML for
  `hx-*` attributes/target ids and response headers (`HX-Redirect`, status codes) — this is the level
  to test new routes, new fragments, and new htmx wiring at.
- **Business-logic tests** (`test_business_logic.py`): call `business_logic.*` directly against the
  `File*` adapters — the preferred level for new permission-check/domain-rule coverage (there is no
  JSON API surface left to test against; commit `bc30eb0` migrated tests to this level for that
  reason).
- **Presentation tests** (`test_presentation.py`): pure function tests over view-model construction,
  including the `Cell.visible`/`kind` computation — add cases here when adding/changing a column's
  visibility or rendering logic.
- **Adapter tests** (`tests/adapters/`): one file per adapter; test the adapter in isolation.
- **e2e tests** (`tests/e2e/`, marked `e2e`, excluded by default via `-m "not e2e"`): require a live
  deployed environment (`E2E_BASE_URL` etc.) — do not expect these to run in a normal dev loop.
- **frontend tests** (`tests/frontend/`, marked `frontend`, excluded the same way): the only
  browser-level coverage there is. They drive whatever `--base-url` names and import nothing from
  the application, so the same suite runs against the dev stack, the stack CI provisions, and an
  installed system. Assert through the `sign_in`/`signed_in`/`sign_in_as`/`select_school`/`list_school` helpers
  in their `conftest.py` rather than re-deriving the login flow or the htmx swap in a test, and
  take directory contents from the `school`/`listed_user` fixtures rather than hardcoding
  `dev/data` values — a literal
  school or username is what pins a test to one deployment. Given `--kelvin_url`, `seed.py` puts
  those contents into the directory itself; it never deletes a user, and its module docstring
  explains why re-creating one breaks the next run's login.
- Fixture data: `tests/data/*.json` is a small, test-owned mirror of `dev/data/*.json`'s shape,
  deliberately decoupled so tests don't depend on whatever is currently in `dev/data`
  (commit `3180c6a`). The `restore_data_files` autouse fixture snapshots/restores any file a `File*`
  adapter writes during a test — you don't need to manually reset fixture state between tests.
- `pytest_configure` in `conftest.py` compiles `.po` → `.mo` before the suite runs, so translation
  tests exercise the real catalog.

### Proportionate validation by change type

| Change | Minimum validation |
| --- | --- |
| Docs-only (`docs/`, `dev/docs/`, `README.md`) | `dev/dev_run.sh pre-commit run -a` (pymarkdown, reuse) |
| Business logic / permission rules | `dev/dev_run.sh task pytest` targeted at `test_business_logic.py` (+ full `task pytest` before finishing, given the 100% coverage gate) |
| Template/fragment/htmx wiring only | Targeted `test_routes.py` run; add or extend a `tests/frontend/` test when the interaction is non-trivial, since that is the only level where the swap actually runs |
| New/changed view model or table column | `test_presentation.py` for the `visible`/`kind` computation + `test_routes.py` for the rendered HTML |
| New adapter or port method | The relevant `tests/adapters/test_*.py` + `test_adapter_registry.py` if wiring changed |
| New translatable string | `dev/dev_run.sh task translate` (fails loudly on untranslated/fuzzy strings) before running tests |
| Any backend code change | Full `dev/dev_run.sh task pytest`, since CI enforces 100% coverage on non-omitted files |
| App Center preinst (`appcenter-management/templates/`, `scripts/generate-preinst`) | `bats appcenter-management/tests/` (needs `bats` and Python >= 3.10; CI job `test_appcenter_scripts`) |
| App Center / Cerbos policy change (`appcenter-management/files/policies/`) | `dev/dev_run.sh task cerbos-compile` (also wired into pre-commit as manual stage `cerbos-policy-check-docker`) — lints/tests via `cerbos compile`, using each policy's `*_test.yaml` |

## Generated and Sensitive Files

- **Do not hand-edit**: `ucsschool-accounts/locales/de/LC_MESSAGES/*.mo` (compiled, git-ignored —
  regenerate with `dev/dev_run.sh task translate`), anything under `.cache/` (git-ignored build/test
  cache), `appcenter-management/preinst` (git-ignored, generated by
  `appcenter-management/scripts/generate-preinst` from `templates/preinst.tmpl`). Note: `README.md`
  says `inst` is generated from `templates/inst.tmpl` — that template doesn't exist in this tree and
  `inst` is a normal tracked file; treat the README claim as stale and confirm before editing `inst`
  as if it were hand-authored.
- **Vendored, not authored here**: `ucsschool_accounts/static/vendor/{htmx,alpine}.min.js` and
  `univention-design-system.{css,js}`. Upgrading these means replacing the vendored file and its
  `.license` sidecar (see commit `19772ef`), not patching them in place.
- **Secrets / local-only**: `dev/.env` (git-ignored, created from `dev/.env.example`) and anything
  under `dev/local/` (git-ignored, e.g. downloaded CA certs). Never commit real secrets into
  `dev/.env.example` — it only holds dev-safe placeholder values (`dev-cookie-secret-change-me`, etc.).
- **`*.license` sidecar files**: required by the `reuse` tool for any file it can't auto-annotate
  (JSON fixtures, binary assets, `.po` files). Generate with `dev/dev_run.sh task reuse`; if reuse
  still fails afterward, create the `.license` file by hand following the existing ones' format.
- `ucsschool-accounts/uv.lock` is managed by `uv` and checked by a pre-commit `uv-lock` hook — don't edit by hand. To add a dependency, run
  `uv add <package>` inside the relevant package directory, which updates that package's
  `pyproject.toml` and lockfile together, instead of editing either file manually.

## Documentation and Changelog Requirements

- New user-facing strings: wrap in `_()`, then run `dev/dev_run.sh task translate` — it will report
  any untranslated/fuzzy entries in `locales/de/LC_MESSAGES/ucsschool-accounts.po` for you to
  fill in before it will compile the `.mo` file.
- User-visible changes should update `docs/ucsschool-accounts/changelog.rst`, as the QA
  checklist in [README.md](README.md#qa-checklist) asks. It is the only changelog: the
  `build_changelog_html` CI job renders it into `changelog.html`, which
  `appcenter-management/README_UPDATE_{DE,EN}.jinja` extend for the App Center. Don't hand-write
  `README_UPDATE_*` files; run `appcenter-management/scripts/build-changelog-html` in the sphinx
  image to preview the result.
- Architectural or HTMX-pattern changes of any significance should be reflected in
  [dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) (it is maintained as a living design
  doc, not a point-in-time snapshot — it currently documents up to commit `176b03d`).
- Sphinx manual changes (`docs/ucsschool-accounts/`) are validated in CI by
  `docs:linkcheck`, `docs:spelling` (uses `spelling_wordlist`), `docs:html`, and `docs:pdf` jobs, all
  gated on changes under that path. They come from the `sphinx-docs` component of `ci-components`;
  configure them through its inputs in `.gitlab-ci/gitlab-ci.yml`, not by adding jobs. The `pages`
  job publishes the default branch's build to the project's GitLab Pages site.

## Common Pitfalls

- Branching page content on `HX-Request` alone, or without `Vary` —
  a history restore and a cached back navigation then get a fragment where the page belongs
  (§ HTMX Request and Rendering Model).
- Rendering a table cell without going through `presentation.py`'s `visible`/`kind` computation —
  this bypasses the mechanism that makes leaking an unauthorized attribute structurally impossible.
- Assuming the school/class/work-group option filtering scales: the query happens in-memory over
  every option on every keystroke (a known, explicitly-commented stopgap in `routes.py`) — don't copy
  the pattern into a new endpoint without checking whether the persistence port should grow a real
  query parameter instead.
- Adding a new adapter/persistence branch by checking an env var directly in `business_logic.py` or
  `routes.py` instead of adding it to `AdapterSelection`/`adapter_registry.py`.
- Leaving a new `_()`-wrapped string untranslated — CI's translation check (and `task translate`
  locally) will fail the build, not just warn. Templates are covered by that check too.
- Forgetting that CI requires **100% coverage** on any file not explicitly listed in
  `[tool.coverage.run] omit` — an uncovered branch in new code fails `accounts-test`, not
  just a manually-run local suite.
- Editing `appcenter-management/preinst` directly — it's generated; edit
  `appcenter-management/templates/preinst.tmpl` and run `./scripts/generate-preinst`.
- Moving an import into `if TYPE_CHECKING:` and leaving its annotation unquoted in a file without
  `from __future__ import annotations` — this raises `NameError` at import time (not just a
  type-checker warning), since the annotation is evaluated eagerly. See § Coding Conventions.

## Definition of Done

Before considering a change complete:

- [ ] Relevant tests updated/added at the appropriate layer (§ Testing and Validation) — prefer
      `business_logic`/`presentation` level over route-level for new domain rules, and route-level
      for new htmx wiring.
- [ ] `dev/dev_run.sh task pytest` passes locally (full run — the CI coverage gate is 100% on
      non-omitted files, so a partial run can hide a coverage failure).
- [ ] `dev/dev_run.sh pre-commit run -a` passes (black, ruff, basedpyright, bandit, reuse, pymarkdown,
      translation check, uv-lock check, OPA checks if `appcenter-management/files/conditions/`
      changed).
- [ ] Any new user-facing string is translated (`task translate` reports no fuzzy/untranslated
      entries).
- [ ] If the change affects install/update behavior or is otherwise QA-relevant,
      `docs/ucsschool-accounts/changelog.rst` is updated.
- [ ] If the change alters the HTMX request/rendering model or a documented architectural boundary,
      [dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) is updated to match.
- [ ] Commit message is Conventional-Commits-formatted and includes an `Issue <project>#<number>` (or
      `Bug #<number>`) trailer.
