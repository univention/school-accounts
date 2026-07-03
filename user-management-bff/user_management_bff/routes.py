# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.

All routes require an authenticated session via the ``current_actor`` dependency,
except the interactive-login routes (login / callback / logout), which establish
or tear down that session.
"""
from functools import partial

from fastapi import APIRouter, Depends, Query, Request
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

templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Build static asset URLs relative to the UI prefix (StaticFiles is mounted at
# ``{FRONTEND_PREFIX}/static`` in main.py).
templates.env.globals["static"] = lambda path: f"{FRONTEND_PREFIX}/static/{path}"
# Expose the UI prefix so templates can build ``hx-*`` URLs to other routes.
templates.env.globals["frontend_prefix"] = FRONTEND_PREFIX

router = APIRouter(prefix=FRONTEND_PREFIX)

# Module-level dependency callables so tests can target them via
# ``app.dependency_overrides``.
auth_port = port_dep(FastAPIAuthenticationPort)
users_persistence = port_dep(UsersPersistencePort)
schools_persistence = port_dep(SchoolsPersistencePort)
school_classes_persistence = port_dep(SchoolClassesPersistencePort)
work_groups_persistence = port_dep(WorkGroupsPersistencePort)
permissions = port_dep(PermissionsPort)


async def current_actor(request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)) -> str:
    """Resolve the authenticated actor id, or raise ``NotAuthenticatedError``."""
    return await auth.get_authenticated_id(request)


def render(request: Request, name: str, **context) -> HTMLResponse:
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
    next: str = "",
    auth: FastAPIAuthenticationPort = Depends(auth_port),
) -> Response:
    """Begin the interactive login: redirect to Keycloak (auth code + PKCE)."""
    return await auth.login_redirect(request, next)


@router.get(AUTH_CALLBACK_PATH)
async def auth_callback(
    request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)
) -> Response:
    """Handle the Keycloak redirect: create the session and set the cookie."""
    return await auth.complete_login(request)


@router.api_route(AUTH_LOGOUT_PATH, methods=["GET", "POST"])
async def logout(request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)) -> Response:
    """End the local session and redirect into Keycloak's RP-initiated logout."""
    return await auth.logout(request)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def shell(request: Request, actor: str = Depends(current_actor)) -> Response:
    """Land on the user list (requires an authenticated session)."""
    return RedirectResponse(f"{FRONTEND_PREFIX}/users", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    school: str | None = None,
    school_classes: list[str] = Query(default=[]),
    work_groups: list[str] = Query(default=[]),
    actor: str = Depends(current_actor),
    users_adapter: UsersPersistencePort = Depends(users_persistence),
    schools_adapter: SchoolsPersistencePort = Depends(schools_persistence),
    school_classes_adapter: SchoolClassesPersistencePort = Depends(school_classes_persistence),
    work_groups_adapter: WorkGroupsPersistencePort = Depends(work_groups_persistence),
    permissions_adapter: PermissionsPort = Depends(permissions),
) -> HTMLResponse:
    """Render the list view.

    Without a ``school`` query parameter this is the empty landing page. When
    ``school`` (and optionally ``school_classes``/``work_groups``) are present,
    the same page is rendered with those filters preselected and the matching
    results already filled in, so a searched URL is a shareable deep link. The
    search form pushes that URL via ``hx-push-url`` while swapping only the
    results region.
    """
    lang = get_lang(request)
    schools = await business_logic.get_schools(
        schools_adapter, permissions_adapter, users_adapter, actor, lang
    )
    school_options = presentation.build_school_options(schools)

    if school is None:
        return render(
            request,
            "pages/user_list.html",
            schools=school_options,
            selected_school=None,
            selected_school_label="",
            school_classes=[],
            work_groups=[],
            view=presentation.empty_user_list_view(lang),
        )

    # A deep link can outlive its school; only load the dependent filters for a
    # school that still exists (the File adapter raises on an unknown id).
    known_school = any(option.value == school for option in school_options)
    class_options: list[presentation.Option] = []
    work_group_options: list[presentation.Option] = []
    if known_school:
        class_options = presentation.build_options(
            await business_logic.get_school_classes(
                school_classes_adapter, permissions_adapter, users_adapter, actor, school, lang
            ),
            selected=school_classes,
        )
        work_group_options = presentation.build_options(
            await business_logic.get_work_groups(
                work_groups_adapter, permissions_adapter, users_adapter, actor, school, lang
            ),
            selected=work_groups,
        )
    data = await business_logic.get_users(
        users_adapter,
        schools_adapter,
        school_classes_adapter,
        work_groups_adapter,
        permissions_adapter,
        actor,
        UsersGetRequest(school=school, school_classes=school_classes, work_groups=work_groups),
        lang,
    )
    return render(
        request,
        "pages/user_list.html",
        schools=school_options,
        selected_school=school,
        selected_school_label=next(
            (option.label for option in school_options if option.value == school), school
        ),
        school_classes=class_options,
        work_groups=work_group_options,
        view=presentation.build_user_list(data, lang),
    )


@router.get("/users/filters", response_class=HTMLResponse)
async def users_filters(
    request: Request,
    school: str,
    actor: str = Depends(current_actor),
    school_classes_adapter: SchoolClassesPersistencePort = Depends(school_classes_persistence),
    work_groups_adapter: WorkGroupsPersistencePort = Depends(work_groups_persistence),
    permissions_adapter: PermissionsPort = Depends(permissions),
    users_adapter: UsersPersistencePort = Depends(users_persistence),
) -> HTMLResponse:
    """Return the class/work-group filter options for the selected school (cascade)."""
    lang = get_lang(request)
    school_classes = await business_logic.get_school_classes(
        school_classes_adapter, permissions_adapter, users_adapter, actor, school, lang
    )
    work_groups = await business_logic.get_work_groups(
        work_groups_adapter, permissions_adapter, users_adapter, actor, school, lang
    )
    return render(
        request,
        "fragments/user_filters.html",
        selected_school=school,
        school_classes=presentation.build_options(school_classes),
        work_groups=presentation.build_options(work_groups),
    )


# NOTE: The ``q`` filtering in the three handlers below is applied in-memory in the
# presentation layer over the full option list the adapter returns. This is a
# stopgap: the persistence ports (schools/school-classes/work-groups) should grow
# a query parameter so the filtering happens at the data source, avoiding fetching
# and permission-checking every option on each keystroke.
@router.get("/users/schools", response_class=HTMLResponse)
async def users_school_options(
    request: Request,
    q: str = "",
    actor: str = Depends(current_actor),
    users_adapter: UsersPersistencePort = Depends(users_persistence),
    schools_adapter: SchoolsPersistencePort = Depends(schools_persistence),
    permissions_adapter: PermissionsPort = Depends(permissions),
) -> HTMLResponse:
    """Return the school combobox options filtered by the typed query (``u-search``)."""
    lang = get_lang(request)
    schools = await business_logic.get_schools(
        schools_adapter, permissions_adapter, users_adapter, actor, lang
    )
    return render(
        request,
        "fragments/school_options.html",
        schools=presentation.build_school_options(schools, query=q),
    )


@router.get("/users/school-classes", response_class=HTMLResponse)
async def users_school_class_options(
    request: Request,
    school: str = "",
    q: str = "",
    actor: str = Depends(current_actor),
    school_classes_adapter: SchoolClassesPersistencePort = Depends(school_classes_persistence),
    permissions_adapter: PermissionsPort = Depends(permissions),
    users_adapter: UsersPersistencePort = Depends(users_persistence),
) -> HTMLResponse:
    """Return the class multiselect options for a school, filtered by query (``u-search``)."""
    lang = get_lang(request)
    options: list[presentation.Option] = []
    # No school selected yet (e.g. typing before a school is chosen) → no options.
    if school:
        school_classes = await business_logic.get_school_classes(
            school_classes_adapter, permissions_adapter, users_adapter, actor, school, lang
        )
        options = presentation.build_options(school_classes, query=q)
    return render(request, "fragments/school_class_options.html", school_classes=options)


@router.get("/users/work-groups", response_class=HTMLResponse)
async def users_work_group_options(
    request: Request,
    school: str = "",
    q: str = "",
    actor: str = Depends(current_actor),
    work_groups_adapter: WorkGroupsPersistencePort = Depends(work_groups_persistence),
    permissions_adapter: PermissionsPort = Depends(permissions),
    users_adapter: UsersPersistencePort = Depends(users_persistence),
) -> HTMLResponse:
    """Return the work-group multiselect options for a school, filtered by query (``u-search``)."""
    lang = get_lang(request)
    options: list[presentation.Option] = []
    # No school selected yet (e.g. typing before a school is chosen) → no options.
    if school:
        work_groups = await business_logic.get_work_groups(
            work_groups_adapter, permissions_adapter, users_adapter, actor, school, lang
        )
        options = presentation.build_options(work_groups, query=q)
    return render(request, "fragments/work_group_options.html", work_groups=options)
