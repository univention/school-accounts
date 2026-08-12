# Repository Guidelines

## Project Overview

UCS@school User Management: a single deployable app (`ucsschool-user-management`) combining a
Python/FastAPI backend-for-frontend with a server-rendered HTMX UI, plus the UCS "App Center"
packaging that installs it into a UCS@school domain. There is **no separate frontend project** —
the old Vue SPA (`user-management-ui/`) was removed; see
[dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) for the full port history and design
rationale. That document is the authoritative deep-dive; this file is the operational summary —
read the former before making any non-trivial UI/architecture change.

Top-level areas:

- [user-management-bff/](user-management-bff/) — the application: FastAPI + Jinja2 + htmx. Nearly
  all day-to-day work happens here.
- [appcenter-management/](appcenter-management/) — UCS App Center install/config scripts, Docker
  Compose templates, and Cerbos authorization policies (`.yaml` resource/derived-role policies under
  `appcenter-management/files/policies/`, registered in LDAP on join as a Guardian policy bundle for
  a Cerbos-hosting listener to pick up — see `appcenter-management/inst`/`templates/preinst.tmpl`).
  Independent from the BFF's own permission adapter (§ Architecture) — only touch this when changing
  how the app is *installed* or how Cerbos policies are evaluated for this app, not for
  UI/business-logic changes.
- [docs/ucsschool-user-management-module/](docs/ucsschool-user-management-module/) — the published
  Sphinx user manual (installation, configuration, troubleshooting, changelog). User-facing, built
  in CI (`docs-*` jobs); not developer documentation.
- [dev/](dev/) — local dev environment (Docker Compose, Keycloak provisioning, fixture data,
  scripts, product/e2e tests). See § Development Environment.

## Repository Structure (`user-management-bff/`)

```text
user_management_bff/
  main.py                   FastAPI app, middleware, global exception -> HTML handlers
  routes.py                 all UI routes (thin handlers), render() helper
  business_logic.py         domain rules + permission checks; no I/O of its own, calls only ports
  presentation.py           shapes business_logic results into template view models
  ports.py                  abstract port interfaces (persistence, auth, permissions, session, ...)
  adapter_registry.py       binds ports -> concrete adapter classes via env vars; port_dep() DI helper
  adapters/                 concrete adapters: Kelvin/File persistence, Guardian/File permissions,
                             Keycloak cookie-session auth + dev/test auth doubles, in-memory sessions
  models.py                 domain models (User, School, SessionRecord, Permission, UsersGetRequest, ...)
  constants.py               env-var-driven config: frontend prefix, auth paths, session-secret
                             loading, supported languages
  correlation_id.py          request correlation-id ContextVar, read by the logging middleware
  logging.py                 loguru configuration
  utils.py                  misc utils (currently just OAuth2 discovery via get_oauth2_settings)
  errors.py                 domain exceptions (PermissionsError, ObjectNotFoundError, ...)
  lang.py                   gettext-based i18n; _() translation helper
  templates/
    base.html                root layout: <head>, vendored asset tags, {% block body %}
    pages/                    full-page templates (user_list, message)
    fragments/                htmx partials (user_table, user_filters, school_options, group_options, toast)
    macros/                   layout.py-style Jinja macros: page_header/toast, cell() cell-kind dispatch
  static/vendor/             vendored htmx, Alpine.js, Univention design-system (CSS/JS/web components)
locales/                    gettext catalogs (de/LC_MESSAGES/...) — sibling of user_management_bff/, not nested under it
keycloak_provisioning/       separate Typer CLI: seeds Keycloak realms/clients/users for dev/test only;
                             unrelated to the adapters above, not for production use
tests/
  adapters/                  adapter-level tests (one file per adapter)
  e2e/                       Playwright-driven backend e2e tests, marked `e2e`, require a live env
  keycloak_provisioning/     tests for the provisioning CLI
  data/                      small, test-owned JSON fixtures (mirror of dev/data/*.json shape)
  test_routes.py             route/HTTP-level tests: TestClient + dependency_overrides, assert on
                             rendered HTML, hx-* attributes, and response headers
  test_adapter_registry.py, test_business_logic.py, test_presentation.py, test_utils.py, test_lang.py, ...
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
  authoritative. The old `GUARDIAN_PERMISSIONS_ADAPTER__GUARDIAN_URL` env var (and the
  `ucsschool-user-management/guardian/url` UCR variable that used to back it) are gone; `compose.jinja`
  now hardcodes `CERBOS_PERMISSIONS_ADAPTER__CERBOS_TARGET: 'cerbos:3593'`, a bare `host:port` gRPC
  target rather than a URL, with no UCR variable/App Center setting behind it and no OAuth2 step
  anymore.
- Which adapter backs each port is selected only via `USER_MANAGEMENT__ADAPTER__*` env vars
  (`dev/.env.example` documents all of them); never gate adapter choice on anything else.

## Logging, Correlation IDs, and Sessions

- **Logging**: use loguru's structured form — `logger.<level>(message, key=value, ...)`, not
  f-strings/`.format()` (the OIDC callback handler in `authentication.py` is the one existing
  exception to this — don't copy it). Log from `business_logic.py` and adapters, never from
  `routes.py` (no logger calls exist there today). Rough level convention: `debug` for routine
  data fetches, `info` for session lifecycle events, `warning`/`error` for failures with enough
  context to trace.
- **Correlation ID** (`correlation_id.py`): a `ContextVar` set once per request by `main.py`'s
  middleware (from the `X-Request-ID` header or a generated UUID), automatically attached to
  every loguru call in that request and echoed back as a response header. This is transparent
  for normal request-scoped code — no action needed — but it will **not** propagate into a
  manually spawned background task/thread that outlives the request's async context.
- **Sessions are three distinct concepts — don't conflate them**: Starlette's
  `SessionMiddleware` cookie holds only transient OAuth `state`/PKCE `code_verifier` during
  login; the actual authenticated session lives behind `SessionStorePort`/
  `InMemorySessionStoreAdapter` (`ports.py`, `adapters/`), keyed by an opaque ID in a separately
  signed cookie; and `adapters/base.py`'s per-request `self.kelvin_session` is unrelated — just
  the HTTP session used for a single Kelvin API call. A new adapter author searching for
  "session" should be sure they're looking at the right one.

## HTMX Request and Rendering Model

- **Every response is HTML.** `main.py` sets `default_response_class=HTMLResponse` and
  `openapi_url=None` — there is no JSON API surface. Do not add JSON endpoints; extend the HTML/htmx
  pattern instead.
- **No per-route `HX-Request` branching for page content.** The list route (`GET /users`) always
  renders the *complete* `pages/user_list.html`; the htmx form uses `hx-select="#results-region"` to
  extract just the results client-side (`templates/pages/user_list.html`). This makes filtered URLs
  directly bookmarkable/shareable (`hx-push-url="true"`) — a bare `GET /users?school=...` reproduces
  the same state a click would. Prefer this `hx-select` pattern over adding `HX-Request` checks when
  a full page and its htmx-triggered update should show identical content.
- `HX-Request` **is** checked, but only in the global error/redirect handling (`main.py:_html_error`,
  `not_authenticated_exception_handler`) and nowhere else — keep it that way; don't sprinkle
  `request.headers.get("HX-Request")` checks into individual route handlers.
- **No mutating routes currently exist** — the app is read-only (search/list only, first-release
  scope). When a mutating endpoint is reintroduced, a success response should return
  `Response(status_code=200, headers={"HX-Redirect": ...})` (which htmx follows client-side) rather
  than JSON or a raw redirect status, consistent with how `NotAuthenticatedError` already uses
  `HX-Redirect` below.
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

There are currently **no mutating routes** in the app — it is read-only (search/list only, this is
the first-release scope; the previous user detail/edit view, its CSRF check, and its form-handling
code were removed in the `drop unused code` refactor). Permission errors from `business_logic` are
still raised as `PermissionsError` and turned into a 403 toast by the global handler — don't
catch/render these manually in route handlers — but there is no form submission path to describe
beyond that today.

## JavaScript and Asset Boundaries

- **Alpine.js is vendored and loaded on every page but currently unused anywhere** (no `x-data` in
  any template). All client-side interactivity today comes from the Univention design-system's
  custom elements (`<u-combobox>`, `<u-multiselect>`, `<u-table>`, ...) firing DOM events (`u-search`,
  `u-change`) that htmx listens for via `hx-trigger` — there is no repo-authored JavaScript file.
  Prefer this event-driven htmx pattern; reach for Alpine only for behavior that genuinely can't be
  expressed as an htmx-observable DOM event, and don't add a new JS bundling/build step without
  discussing it first (none exists today).
- htmx, Alpine, and the design-system bundle are **vendored** under
  `user_management_bff/static/vendor/` (not installed via pip/npm). See § Generated and Sensitive
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
    changes are picked up live. Requires `user-management-proxy` to resolve (add it to `/etc/hosts`).
    UI: `http://user-management-proxy/univention/ucsschool/user-management/ui/`. API docs:
    `.../bff/docs`. Keycloak admin: `.../keycloak/admin/` (`admin:admin`).
  - `pytest` — unit/integration tests (excludes `e2e`-marked tests); accepts up to 7 extra pytest
    args, e.g. `dev/dev_run.sh task pytest --pdb`.
  - `pytest-e2e` — Playwright-backed backend e2e tests against a real deployed environment; requires
    `E2E_BASE_URL`, `E2E_CERBOS_URL`, `E2E_KELVIN_URL` and resolvable domain names (see
    [README.md](README.md#running-e2e-tests-for-the-backend)). Not runnable standalone locally.
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
- Product tests (`dev/tests/product-tests/`) are a separate Python project (own `pyproject.toml` /
  `uv.lock`), Playwright-driven, run against a fully installed instance — not part of the normal
  backend test loop.

## Common Commands

All commands below are `dev/dev_run.sh` invocations (run from the repo root) unless noted; they wrap
docker compose so no local Python/Node install is required.

| Goal | Command |
| --- | --- |
| Run backend unit/integration tests | `dev/dev_run.sh task pytest` |
| Run a single test file/case | `dev/dev_run.sh task pytest user-management-bff/tests/test_routes.py::test_users_search_renders_results` |
| Run backend e2e tests | see § Development Environment — requires a live `E2E_*` environment |
| Run all pre-commit hooks (lint/format/type-check/license/translation) | `dev/dev_run.sh pre-commit run -a` |
| Run pre-commit only on staged files | `dev/dev_run.sh pre-commit run` |
| Precise type check (basedpyright, matches CI) | `uvx prek run --hook-stage manual basedpyright-bff-container-baseline --all-files` |
| Start the dev server | `dev/dev_run.sh task dev-server` |
| Start a local Cerbos server (manual policy/adapter testing) | `dev/dev_run.sh task cerbos-server` |
| Lint/test the Cerbos policies (`cerbos compile`) | `dev/dev_run.sh task cerbos-compile` |
| Regenerate/verify translations | `dev/dev_run.sh task translate` |
| Generate license headers | `dev/dev_run.sh task reuse` |
| Serve the Sphinx manual locally | `dev/dev_run.sh task sphinx` |
| Clean dev artifacts/containers | `dev/dev_run.sh task clean` |
| Regenerate the App Center `inst` script | `cd appcenter-management && ./scripts/generate-preinst` |

CI (`.gitlab-ci/gitlab-ci.yml`) runs the equivalent of `pytest -m "not e2e"` with **coverage gated via
the `BFF_COVERAGE_LIMIT` CI variable (currently `"100"`, i.e. 100%)** over `user_management_bff` +
`keycloak_provisioning` (excluding `main.py`, `constants.py`, `logging.py` — see
`[tool.coverage.run] omit` in `pyproject.toml`). New code outside those three omitted files must be
fully covered or CI fails.

## Coding Conventions

Enforced by tooling (pre-commit, see `.pre-commit-config.yaml`) — treat these as required, not
optional:

- **black** (line length 105, target py311) and **ruff** (`E, F, I, B`, `B008`/`B904` ignored,
  `--fix`) — both configured in `user-management-bff/pyproject.toml`.
- **basedpyright** on the package (config: `user-management-bff/pyrightconfig.json`,
  `dev/tests/product-tests/pyrightconfig.json`) with a committed baseline
  (`basedpyright-baseline.json` per package) suppressing pre-existing findings — only *new*
  diagnostics fail the pre-commit hook/CI job. The default `basedpyright-*-native-baseline` hooks run
  against the host's `uv`-managed venv; for a precise type check that matches CI exactly, run the
  containerized hook instead: `uvx prek run --hook-stage manual basedpyright-bff-container-baseline
  --all-files` (swap in `basedpyright-product-tests-container-baseline` for
  `dev/tests/product-tests/`). These container hooks are `stages: [manual]`, so `pre-commit run -a`
  alone skips them — invoke them explicitly when you want a trustworthy type-check result.
- **bandit** on everything except `tests/` and `appcenter-management/scripts/test_*`.
- **reuse** — every source file needs an SPDX header or a matching `.license` sidecar file (see the
  many `*.license` files already in the tree for the pattern).
- **pymarkdown** on Markdown files (arbitrary line length, duplicate headings, bare URLs, and
  missing-top-heading rules are disabled; other rules apply).
- Commit messages: **Conventional Commits, strictly enforced** (`conventional-pre-commit --strict`),
  plus a required issue reference trailer (`Issue <project>#<number>` or `Bug #<number>`) checked by
  the local `issue-reference` hook.
- User-facing strings must be wrapped in `_()` from `user_management_bff.lang` (see
  `from user_management_bff.lang import _`) so they flow into the translation catalog — see next
  section for the follow-up step this requires.

**Type-only imports go under `if TYPE_CHECKING:`** — not gated by a specific tool, but treat as
required, since getting it wrong is a real runtime bug rather than a lint nit. An import used
exclusively inside type annotations — never instantiated/called, never a base class, never in an
`isinstance`/`except` clause, and never the right-hand side of a module-level
`X: TypeAlias = ...` assignment — belongs in the `if TYPE_CHECKING:` block, not as a top-level
import. Whether that requires quoting the annotation depends on the file:

- Without `from __future__ import annotations` at the top, annotations are evaluated eagerly at
  `def`/class time, so any annotation referencing a `TYPE_CHECKING`-only name must be a quoted
  string, e.g. `-> "SomeType"` (see `adapters/permissions.py`'s `_attrs_to_struct_fields`, whose
  return type references `MessageMap` this way).
- With `from __future__ import annotations` present (as in most `tests/` files), all annotations
  are deferred/stringified automatically — no quoting needed.
- Don't move a name that's genuinely evaluated at runtime — e.g. the RHS of a module-level
  `TypeAlias`, a decorator, a base class, an `except`/`isinstance` target, or anything actually
  constructed/called in a method body. That raises `NameError` at import time once `TYPE_CHECKING`
  is `False`, not just a type-checker complaint.

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
| Template/fragment/htmx wiring only | Targeted `test_routes.py` run; manually check the swap in the dev server if the interaction is non-trivial (no browser-level htmx assertions exist beyond checking rendered attributes) |
| New/changed view model or table column | `test_presentation.py` for the `visible`/`kind` computation + `test_routes.py` for the rendered HTML |
| New adapter or port method | The relevant `tests/adapters/test_*.py` + `test_adapter_registry.py` if wiring changed |
| New translatable string | `dev/dev_run.sh task translate` (fails loudly on untranslated/fuzzy strings) before running tests |
| Any backend code change | Full `dev/dev_run.sh task pytest`, since CI enforces 100% coverage on non-omitted files |
| App Center / Cerbos policy change (`appcenter-management/files/policies/`) | `dev/dev_run.sh task cerbos-compile` (also wired into pre-commit as manual stage `cerbos-policy-check-docker`) — lints/tests via `cerbos compile`, using each policy's `*_test.yaml` |

## Generated and Sensitive Files

- **Do not hand-edit**: `user-management-bff/locales/de/LC_MESSAGES/*.mo` (compiled, git-ignored —
  regenerate with `dev/dev_run.sh task translate`), anything under `.cache/` (git-ignored build/test
  cache), `appcenter-management/preinst` (git-ignored, generated by
  `appcenter-management/scripts/generate-preinst` from `templates/preinst.tmpl`). Note: `README.md`
  says `inst` is generated from `templates/inst.tmpl` — that template doesn't exist in this tree and
  `inst` is a normal tracked file; treat the README claim as stale and confirm before editing `inst`
  as if it were hand-authored.
- **Vendored, not authored here**: `user_management_bff/static/vendor/{htmx,alpine}.min.js` and
  `univention-design-system.{css,js}`. Upgrading these means replacing the vendored file and its
  `.license` sidecar (see commit `19772ef`), not patching them in place.
- **Secrets / local-only**: `dev/.env` (git-ignored, created from `dev/.env.example`) and anything
  under `dev/local/` (git-ignored, e.g. downloaded CA certs). Never commit real secrets into
  `dev/.env.example` — it only holds dev-safe placeholder values (`dev-cookie-secret-change-me`, etc.).
- **`*.license` sidecar files**: required by the `reuse` tool for any file it can't auto-annotate
  (JSON fixtures, binary assets, `.po` files). Generate with `dev/dev_run.sh task reuse`; if reuse
  still fails afterward, create the `.license` file by hand following the existing ones' format.
- `user-management-bff/uv.lock` and `dev/tests/product-tests/uv.lock` are managed by `uv` and checked
  by a pre-commit `uv-lock` hook — don't edit by hand. To add a dependency, run
  `uv add <package>` inside the relevant package directory, which updates that package's
  `pyproject.toml` and lockfile together, instead of editing either file manually.

## Documentation and Changelog Requirements

- New user-facing strings: wrap in `_()`, then run `dev/dev_run.sh task translate` — it will report
  any untranslated/fuzzy entries in `locales/de/LC_MESSAGES/ucsschool-user-management.po` for you to
  fill in before it will compile the `.mo` file.
- User-visible changes should update the release changelogs the QA checklist in
  [README.md](README.md#qa-checklist) explicitly asks for: `appcenter-management/README_UPDATE_DE`,
  `appcenter-management/README_UPDATE_EN`, and `docs/ucsschool-user-management-module/changelog.rst`.
- Architectural or HTMX-pattern changes of any significance should be reflected in
  [dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) (it is maintained as a living design
  doc, not a point-in-time snapshot — it currently documents up to commit `176b03d`).
- Sphinx manual changes (`docs/ucsschool-user-management-module/`) are validated in CI by
  `docs-linkcheck`, `docs-spelling` (uses `spelling_wordlist`), `docs-html`, and `docs-pdf` jobs, all
  gated on changes under that path.

## Common Pitfalls

- Reading `request.headers.get("HX-Request")` inside a route handler to branch page content — the
  established pattern is `hx-select` on an always-full-page response (§ HTMX Request and Rendering
  Model). Only the global error handlers branch on this header.
- Rendering a table cell without going through `presentation.py`'s `visible`/`kind` computation —
  this bypasses the mechanism that makes leaking an unauthorized attribute structurally impossible.
- Assuming the school/class/work-group option filtering scales: the query happens in-memory over
  every option on every keystroke (a known, explicitly-commented stopgap in `routes.py`) — don't copy
  the pattern into a new endpoint without checking whether the persistence port should grow a real
  query parameter instead.
- Adding a new adapter/persistence branch by checking an env var directly in `business_logic.py` or
  `routes.py` instead of adding it to `AdapterSelection`/`adapter_registry.py`.
- Leaving a new `_()`-wrapped string untranslated — CI's translation check (and `task translate`
  locally) will fail the build, not just warn.
- Forgetting that CI requires **100% coverage** on any file not explicitly listed in
  `[tool.coverage.run] omit` — an uncovered branch in new code fails `bff-test`/`bff-coverage`, not
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
- [ ] If the change affects install/update behavior or is otherwise QA-relevant, the changelog files
      listed in § Documentation and Changelog Requirements are updated.
- [ ] If the change alters the HTMX request/rendering model or a documented architectural boundary,
      [dev/docs/htmx-architecture.md](dev/docs/htmx-architecture.md) is updated to match.
- [ ] Commit message is Conventional-Commits-formatted and includes an `Issue <project>#<number>` (or
      `Bug #<number>`) trailer.
