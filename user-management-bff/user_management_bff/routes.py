# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.

All routes require an authenticated session via the ``current_actor`` dependency,
except the interactive-login routes (login / callback / logout), which establish
or tear down that session.
"""

from collections.abc import AsyncIterator
from functools import partial
from typing import Annotated, cast
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.datastructures import FormData
from starlette.responses import RedirectResponse, Response

from . import business_logic, presentation
from .adapter_registry import port_dep
from .adapters.base import kelvin_session_scope
from .constants import (
    AUTH_CALLBACK_PATH,
    AUTH_LOGIN_PATH,
    AUTH_LOGOUT_PATH,
    CSRF_HEADER_NAME,
    FRONTEND_PREFIX,
    TEMPLATES_DIR,
)
from .errors import PermissionsError
from .lang import _, get_lang
from .models import UsersGetRequest
from .ports import (
    FastAPIAuthenticationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)


def _static_url(path: str) -> str:
    return f"{FRONTEND_PREFIX}/static/{path}"


templates = Jinja2Templates(directory=TEMPLATES_DIR)
# `env.globals` is typed against Jinja's default globals (range, dict, cycler, ...),
# so pyright rejects new keys unless we widen the type here.
env_globals = cast("dict[str, object]", templates.env.globals)
# Build static asset URLs relative to the UI prefix (StaticFiles is mounted at
# ``{FRONTEND_PREFIX}/static`` in main.py).
env_globals["static"] = _static_url
# Expose the UI prefix so templates can build ``hx-*`` URLs to other routes.
env_globals["frontend_prefix"] = FRONTEND_PREFIX
# The all-groups sentinel is rendered as an option value, so templates need it too.
env_globals["all_groups_value"] = presentation.ALL_GROUPS


async def kelvin_session() -> AsyncIterator[None]:
    """Give every route one Kelvin session, closed when the response is done.

    Declared on the router so a new route cannot forget it, and so the adapters
    keep their own signatures - they read the scope rather than being handed it.
    """
    async with kelvin_session_scope():
        yield


router = APIRouter(prefix=FRONTEND_PREFIX, dependencies=[Depends(kelvin_session)])

# Module-level dependency callables so tests can target them via
# ``app.dependency_overrides``.
auth_port = port_dep(FastAPIAuthenticationPort)
users_persistence = port_dep(UsersPersistencePort)
schools_persistence = port_dep(SchoolsPersistencePort)
school_classes_persistence = port_dep(SchoolClassesPersistencePort)
work_groups_persistence = port_dep(WorkGroupsPersistencePort)
permissions = port_dep(PermissionsPort)

AuthDep = Annotated[FastAPIAuthenticationPort, Depends(auth_port)]
UsersAdapterDep = Annotated[UsersPersistencePort, Depends(users_persistence)]
SchoolsAdapterDep = Annotated[SchoolsPersistencePort, Depends(schools_persistence)]
SchoolClassesAdapterDep = Annotated[SchoolClassesPersistencePort, Depends(school_classes_persistence)]
WorkGroupsAdapterDep = Annotated[WorkGroupsPersistencePort, Depends(work_groups_persistence)]
PermissionsAdapterDep = Annotated[PermissionsPort, Depends(permissions)]


async def current_actor(request: Request, auth: AuthDep) -> str:
    """Resolve the authenticated actor id, or raise ``NotAuthenticatedError``."""
    actor = await auth.get_authenticated_id(request)
    request.state.actor_name = await auth.get_display_name(request) or actor
    return actor


ActorDep = Annotated[str, Depends(current_actor)]


async def verified_csrf(request: Request, auth: AuthDep) -> None:
    """Reject an unsafe request whose CSRF token is missing or wrong."""
    if not await auth.check_csrf(request, request.headers.get(CSRF_HEADER_NAME)):
        raise PermissionsError(
            _(
                "Invalid or missing security token. Please reload the page and try again.",
                lang=get_lang(request),
            )
        )


CsrfDep = Annotated[None, Depends(verified_csrf)]


def selected_ids(form: FormData) -> list[str]:
    """The user ids the selection form submitted."""
    return [str(value) for value in form.getlist("user_id")]


def render_static(request: Request, name: str, **context: object) -> HTMLResponse:
    """Render chrome that carries no form: the error toast and message page.

    Issues no CSRF token on purpose: the exception handlers use this, and some
    fire *because* authentication is unusable.
    """
    lang = get_lang(request)
    context.setdefault("lang", lang)
    context.setdefault("actor_name", getattr(request.state, "actor_name", ""))
    context["_"] = partial(_, lang=lang)
    return templates.TemplateResponse(request, name, context)


async def render(
    request: Request, name: str, auth: FastAPIAuthenticationPort, **context: object
) -> HTMLResponse:
    """Render ``name`` with the request's language, translation helper and CSRF token bound.

    Templates get ``{{ _("text") }}``, ``{{ lang }}`` and ``{{ csrf_token }}``.
    The token is issued here, not per route; ``render_static`` is the token-less path.
    """
    context.setdefault("csrf_token", await auth.issue_csrf_token(request))
    return render_static(request, name, **context)


@router.get(AUTH_LOGIN_PATH)
async def login(
    request: Request,
    auth: AuthDep,
    next: str = "",
) -> Response:
    """Begin the interactive login: redirect to Keycloak (auth code + PKCE)."""
    return await auth.login_redirect(request, next)


@router.get(AUTH_CALLBACK_PATH)
async def auth_callback(request: Request, auth: AuthDep) -> Response:
    """Handle the Keycloak redirect: create the session and set the cookie."""
    return await auth.complete_login(request)


# POST-only: `SameSite=lax` still sends the cookie on a top-level GET navigation, so a
# cross-site link or a prefetcher could otherwise end the session.
@router.post(AUTH_LOGOUT_PATH)
async def logout(request: Request, auth: AuthDep) -> Response:
    """End the local session and redirect into Keycloak's RP-initiated logout."""
    return await auth.logout(request)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def shell(_request: Request, _actor: ActorDep) -> Response:
    """Land on the user list (requires an authenticated session)."""
    return RedirectResponse(f"{FRONTEND_PREFIX}/users", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    actor: ActorDep,
    users_adapter: UsersAdapterDep,
    schools_adapter: SchoolsAdapterDep,
    school_classes_adapter: SchoolClassesAdapterDep,
    work_groups_adapter: WorkGroupsAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    auth: AuthDep,
    school: str | None = None,
    group: str | None = None,
) -> HTMLResponse:
    """Render the list view, empty or with ``school``/``group`` preselected as a deep link.

    ``group`` is a combined ``kind:id`` value because both datasets share one
    single-select control.
    """
    lang = get_lang(request)
    schools = await business_logic.get_schools(
        schools_adapter, permissions_adapter, users_adapter, actor, lang
    )
    school_options = presentation.build_school_options(schools, selected=school or "")

    if school is None:
        response = await render(
            request,
            "pages/user_list.html",
            auth,
            schools=school_options,
            selected_school=None,
            selected_group=presentation.ALL_GROUPS,
            group_sections=[],
            query="",
            view=presentation.empty_user_list_view(lang),
        )
        response.headers["HX-Push-Url"] = _push_url(None, presentation.ALL_GROUPS)
        return response

    kind, item_id = presentation.split_group_value(group)
    # A deep link can outlive its school; only load the dependent filters for a
    # school that still exists (the File adapter raises on an unknown id).
    known_school = any(option.value == school for option in school_options)
    group_sections: list[presentation.OptionGroup] = []
    if known_school:
        group_sections = await _group_sections(
            school_classes_adapter,
            work_groups_adapter,
            permissions_adapter,
            users_adapter,
            actor,
            school,
            lang,
            selected=f"{kind}:{item_id}" if kind else "",
        )
    # Drop a group the selected school does not have. That covers a stale deep
    # link, and the moment after a school change where the search fires while the
    # dependent control still holds the previous school's selection.
    if kind and not any(o.selected for section in group_sections for o in section.options):
        kind, item_id = "", ""
    # The control always carries a selection, so "no group filter" is the
    # explicit all-groups value rather than an empty one.
    selected_group = f"{kind}:{item_id}" if kind else presentation.ALL_GROUPS
    data = await business_logic.get_users(
        users_adapter,
        schools_adapter,
        school_classes_adapter,
        work_groups_adapter,
        permissions_adapter,
        actor,
        UsersGetRequest(
            school=school,
            school_classes=[item_id] if kind == presentation.SCHOOL_CLASS_KIND else [],
            work_groups=[item_id] if kind == presentation.WORK_GROUP_KIND else [],
        ),
        lang,
    )
    response = await render(
        request,
        "pages/user_list.html",
        auth,
        schools=school_options,
        selected_school=school,
        selected_group=selected_group,
        group_sections=group_sections,
        query="",
        view=presentation.build_user_list(data, lang),
    )
    response.headers["HX-Push-Url"] = _push_url(school, selected_group)
    return response


def _push_url(school: str | None, selected_group: str) -> str:
    """The canonical, shareable URL for a filter state.

    Set unconditionally as ``HX-Push-Url``, which htmx prefers over the request
    URL - that is what drops the all-groups default from the address bar.
    """
    params = {"school": school} if school else {}
    if selected_group != presentation.ALL_GROUPS:
        params["group"] = selected_group
    return f"{FRONTEND_PREFIX}/users" + (f"?{urlencode(params)}" if params else "")


async def _group_sections(
    school_classes_adapter: SchoolClassesPersistencePort,
    work_groups_adapter: WorkGroupsPersistencePort,
    permissions_adapter: PermissionsPort,
    users_adapter: UsersPersistencePort,
    actor: str,
    school: str,
    lang: str,
    selected: str = "",
    query: str = "",
) -> list[presentation.OptionGroup]:
    """Load both filterable datasets for ``school`` as combined filter sections."""
    return presentation.build_group_options(
        await business_logic.get_school_classes(
            school_classes_adapter, permissions_adapter, users_adapter, actor, school, lang
        ),
        await business_logic.get_work_groups(
            work_groups_adapter, permissions_adapter, users_adapter, actor, school, lang
        ),
        lang,
        selected=selected,
        query=query,
    )


@router.get("/users/filters", response_class=HTMLResponse)
async def users_filters(
    request: Request,
    school: str,
    actor: ActorDep,
    auth: AuthDep,
    school_classes_adapter: SchoolClassesAdapterDep,
    work_groups_adapter: WorkGroupsAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    users_adapter: UsersAdapterDep,
) -> HTMLResponse:
    """Return the combined class/work-group filter for the selected school (cascade).

    Swaps the whole control rather than just its items: ``u-list-select`` keeps
    its ``value`` across an item swap, so replacing the element is what drops the
    previous school's selection.
    """
    lang = get_lang(request)
    return await render(
        request,
        "fragments/user_filters.html",
        auth,
        selected_school=school,
        # A fresh school starts unfiltered.
        selected_group=presentation.ALL_GROUPS,
        query="",
        group_sections=await _group_sections(
            school_classes_adapter,
            work_groups_adapter,
            permissions_adapter,
            users_adapter,
            actor,
            school,
            lang,
        ),
    )


# NOTE: The ``q`` filtering in the two handlers below is applied in-memory in the
# presentation layer over the full option list the adapter returns. This is a
# stopgap: the persistence ports (schools/school-classes/work-groups) should grow
# a query parameter so the filtering happens at the data source, avoiding fetching
# and permission-checking every option on each keystroke.
@router.get("/users/schools", response_class=HTMLResponse)
async def users_school_options(
    request: Request,
    actor: ActorDep,
    auth: AuthDep,
    users_adapter: UsersAdapterDep,
    schools_adapter: SchoolsAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    q: str = "",
) -> HTMLResponse:
    """Return the school list-select options filtered by the typed query (``u-search``)."""
    lang = get_lang(request)
    schools = await business_logic.get_schools(
        schools_adapter, permissions_adapter, users_adapter, actor, lang
    )
    return await render(
        request,
        "fragments/school_options.html",
        auth,
        schools=presentation.build_school_options(schools, query=q),
    )


@router.get("/users/groups", response_class=HTMLResponse)
async def users_group_options(
    request: Request,
    actor: ActorDep,
    auth: AuthDep,
    school_classes_adapter: SchoolClassesAdapterDep,
    work_groups_adapter: WorkGroupsAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    users_adapter: UsersAdapterDep,
    school: str = "",
    q: str = "",
) -> HTMLResponse:
    """Return the combined class/work-group items for a school, filtered by query."""
    lang = get_lang(request)
    sections: list[presentation.OptionGroup] = []
    # No school selected yet (e.g. typing before a school is chosen) → no options.
    if school:
        sections = await _group_sections(
            school_classes_adapter,
            work_groups_adapter,
            permissions_adapter,
            users_adapter,
            actor,
            school,
            lang,
            query=q,
        )
    return await render(
        request,
        "fragments/group_options.html",
        auth,
        selected_school=school,
        group_sections=sections,
        # The element keeps its own selection across an item swap, so the
        # fragment does not need to know which value is currently selected.
        selected_group="",
        query=q,
    )


async def _password_reset_dialog(
    request: Request,
    auth: FastAPIAuthenticationPort,
    data: presentation.PasswordResetSelectionData,
    password_error: str = "",
) -> HTMLResponse:
    """The confirmation dialog for a resolved selection, before and after a submit."""
    return await render(
        request,
        "fragments/password_reset_dialog.html",
        auth,
        confirmation=presentation.build_password_reset_confirmation(data, get_lang(request)),
        password_error=password_error,
    )


@router.post("/users/password-reset/confirm", response_class=HTMLResponse)
async def users_password_reset_confirm(
    request: Request,
    actor: ActorDep,
    auth: AuthDep,
    users_adapter: UsersAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    _csrf: CsrfDep,
) -> HTMLResponse:
    """Render the confirmation dialog for the current selection.

    POST despite reading nothing: the id list has no length ceiling and this is a
    transient step, not a shareable URL. Every unsafe method carries the token.
    """
    lang = get_lang(request)
    form = await request.form()
    data = await business_logic.get_password_reset_selection(
        users_adapter,
        permissions_adapter,
        actor,
        selected_ids(form),
        lang,
    )
    return await _password_reset_dialog(request, auth, data)


@router.post("/users/password-reset", response_class=HTMLResponse)
async def users_password_reset(
    request: Request,
    actor: ActorDep,
    auth: AuthDep,
    users_adapter: UsersAdapterDep,
    permissions_adapter: PermissionsAdapterDep,
    _csrf: CsrfDep,
) -> HTMLResponse:
    """Set one password for every selected user (bulk reset).

    Renders a summary toast plus a per-target outcome list.
    """
    lang = get_lang(request)
    form = await request.form()
    result = await business_logic.set_passwords(
        users_adapter,
        permissions_adapter,
        actor,
        selected_ids(form),
        str(form.get("password", "")),
        lang,
        change_on_next_login=bool(form.get("change_on_next_login")),
    )
    rejection = result.password_rejection
    if rejection is not None and result.selection is not None:
        # The password is what needs fixing, so keep the dialog and put the reason on
        # the field. The write already resolved the selection; re-resolving costs a
        # second round of Kelvin reads and a Cerbos batch for nothing.
        response = await _password_reset_dialog(
            request, auth, result.selection, password_error=rejection
        )
        response.headers["HX-Retarget"] = "#password-reset-dialog-region"
        response.headers["HX-Reswap"] = "innerHTML"
        return response

    message, variant = presentation.build_password_reset_summary(result, lang)
    rows = presentation.build_password_reset_outcome_rows(result, lang)
    return await render(
        request,
        "fragments/password_reset_result.html",
        auth,
        message=message,
        variant=variant,
        rows=rows,
    )
