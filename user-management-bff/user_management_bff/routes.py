# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.

All routes require an authenticated session via the ``current_actor`` dependency,
except the interactive-login routes (login / callback / logout), which establish
or tear down that session.
"""

from functools import partial
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, Response

from . import business_logic, presentation
from .adapter_registry import port_dep
from .constants import (
    AUTH_CALLBACK_PATH,
    AUTH_LOGIN_PATH,
    AUTH_LOGOUT_PATH,
    FRONTEND_PREFIX,
    TEMPLATES_DIR,
)
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

router = APIRouter(prefix=FRONTEND_PREFIX)

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
    return await auth.get_authenticated_id(request)


ActorDep = Annotated[str, Depends(current_actor)]


def render(request: Request, name: str, **context: object) -> HTMLResponse:
    """Render ``name`` with the request's language and translation helper bound.

    Templates can call ``{{ _("text") }}`` (translated into the request language)
    and read ``{{ lang }}``.
    """
    lang = get_lang(request)
    context.setdefault("lang", lang)
    context["_"] = partial(_, lang=lang)
    return templates.TemplateResponse(request, name, context)


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


@router.api_route(AUTH_LOGOUT_PATH, methods=["GET", "POST"])
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
    school: str | None = None,
    group: str | None = None,
) -> HTMLResponse:
    """Render the list view.

    Without a ``school`` query parameter this is the empty landing page. When
    ``school`` (and optionally ``group``) are present, the same page is rendered
    with those filters preselected and the matching results already filled in, so
    a searched URL is a shareable deep link. The search form pushes that URL via
    ``hx-push-url`` while swapping only the results region.

    ``group`` carries the combined class/work-group filter as a single
    ``kind:id`` value, because both datasets share one single-select control.
    """
    lang = get_lang(request)
    schools = await business_logic.get_schools(schools_adapter, users_adapter, actor, lang)
    school_options = presentation.build_school_options(schools, selected=school or "")

    if school is None:
        return render(
            request,
            "pages/user_list.html",
            schools=school_options,
            selected_school=None,
            selected_group=presentation.ALL_GROUPS,
            group_sections=[],
            query="",
            view=presentation.empty_user_list_view(lang),
        )

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
    return render(
        request,
        "pages/user_list.html",
        schools=school_options,
        selected_school=school,
        selected_group=selected_group,
        group_sections=group_sections,
        query="",
        view=presentation.build_user_list(data, lang),
    )


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
    return render(
        request,
        "fragments/user_filters.html",
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
    users_adapter: UsersAdapterDep,
    schools_adapter: SchoolsAdapterDep,
    q: str = "",
) -> HTMLResponse:
    """Return the school list-select options filtered by the typed query (``u-search``)."""
    lang = get_lang(request)
    schools = await business_logic.get_schools(schools_adapter, users_adapter, actor, lang)
    return render(
        request,
        "fragments/school_options.html",
        schools=presentation.build_school_options(schools, query=q),
    )


@router.get("/users/groups", response_class=HTMLResponse)
async def users_group_options(
    request: Request,
    actor: ActorDep,
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
    return render(
        request,
        "fragments/group_options.html",
        selected_school=school,
        group_sections=sections,
        # The element keeps its own selection across an item swap, so the
        # fragment does not need to know which value is currently selected.
        selected_group="",
        query=q,
    )
