# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.

All routes require an authenticated session via the ``current_actor`` dependency,
except the interactive-login routes (login / callback / logout), which establish
or tear down that session.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable
from dataclasses import dataclass
from functools import partial
from typing import Annotated, cast
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.datastructures import FormData
from starlette.responses import RedirectResponse, Response

from . import business_logic, presentation
from .adapter_registry import port_dep
from .adapters.base import kelvin_session_scope
from .adapters.request_cache import (
    RequestCachedSchoolClassesAdapter,
    RequestCachedSchoolsAdapter,
    RequestCachedWorkGroupsAdapter,
)
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
# The element a filter change replaces. htmx names it back in ``HX-Target``,
# which is how the list route knows it need only render that much.
RESULTS_REGION_ID = "results-region"


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
PermissionsAdapterDep = Annotated[PermissionsPort, Depends(permissions)]


# Async without an await: FastAPI hands a sync dependency to a threadpool, which
# is real overhead per request for a wrapper that only constructs an object.
#
# The three read-only lookups below are asked for the same school more than once
# per request (filter sidebar and table both need the group display names), so
# each handler gets a memoizing decorator instead of the raw adapter. FastAPI
# resolves a dependency once per request, which is what scopes the cache: every
# parameter of a handler shares one instance, and the next request starts empty.
async def cached_schools_persistence(  # NOSONAR(S7503)
    adapter: Annotated[SchoolsPersistencePort, Depends(schools_persistence)],
) -> SchoolsPersistencePort:
    return RequestCachedSchoolsAdapter(adapter)


async def cached_school_classes_persistence(  # NOSONAR(S7503)
    adapter: Annotated[SchoolClassesPersistencePort, Depends(school_classes_persistence)],
) -> SchoolClassesPersistencePort:
    return RequestCachedSchoolClassesAdapter(adapter)


async def cached_work_groups_persistence(  # NOSONAR(S7503)
    adapter: Annotated[WorkGroupsPersistencePort, Depends(work_groups_persistence)],
) -> WorkGroupsPersistencePort:
    return RequestCachedWorkGroupsAdapter(adapter)


SchoolsAdapterDep = Annotated[SchoolsPersistencePort, Depends(cached_schools_persistence)]
SchoolClassesAdapterDep = Annotated[
    SchoolClassesPersistencePort, Depends(cached_school_classes_persistence)
]
WorkGroupsAdapterDep = Annotated[WorkGroupsPersistencePort, Depends(cached_work_groups_persistence)]


async def current_actor(request: Request, auth: AuthDep) -> str:
    """Resolve the authenticated actor id, or raise ``NotAuthenticatedError``."""
    actor = await auth.get_authenticated_id(request)
    request.state.actor_id = actor
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
            selected_group="",
            group_sections=[],
            query="",
            view=_list_view(None, lang, known_school=False),
        )
        response.headers["HX-Push-Url"] = _push_url(None, "")
        return response

    # htmx asks this route for the whole page and keeps only #results-region
    # (`hx-select`), so a filter change rebuilt the group control - every class
    # and work group of the school, the most expensive thing on the page - and
    # threw it away. Answer such a request with the region it actually takes.
    listing = _Listing(
        users=users_adapter,
        schools=schools_adapter,
        school_classes=school_classes_adapter,
        work_groups=work_groups_adapter,
        permissions=permissions_adapter,
        actor=actor,
        school=school,
        lang=lang,
        known_school=any(option.value == school for option in school_options),
        results_only=(
            request.headers.get("HX-Request") == "true"
            and request.headers.get("HX-Target") == RESULTS_REGION_ID
        ),
    )
    # Listing a whole school is a choice, not the default. Nothing selected means
    # nothing is listed: a school of thousands takes seconds to fetch and seconds
    # more to render, and the bulk reset it feeds refuses more than
    # PASSWORD_RESET_MAX_TARGETS anyway, so nobody should wait for one they did
    # not ask for.
    group_sections, data, selection = await _resolve_listing(listing, _GroupSelection.from_value(group))
    response = await render(
        request,
        "fragments/results_region.html" if listing.results_only else "pages/user_list.html",
        auth,
        schools=school_options,
        selected_school=school,
        selected_group=selection.value,
        group_sections=group_sections,
        query="",
        view=_list_view(data, lang, listing.known_school),
    )
    response.headers["HX-Push-Url"] = _push_url(school, selection.value)
    # One URL, two bodies. A browser going back to a pushed URL may otherwise
    # show the fragment it cached for it as the whole page.
    response.headers.add_vary_header("HX-Request, HX-Target")
    return response


@dataclass(frozen=True)
class _GroupSelection:
    """What the request asked the table to list, once the group value is read.

    Three states, not two: no selection lists nobody, ``all_groups`` lists the
    whole school, and a kind/id pair lists one group. The URL tells them apart,
    so a reload and a shared link land where the click did.
    """

    kind: str = ""
    item_id: str = ""
    all_groups: bool = False

    @classmethod
    def from_value(cls, value: str | None) -> _GroupSelection:
        kind, item_id = presentation.split_group_value(value)
        return cls(kind, item_id, (value or "") == presentation.ALL_GROUPS)

    @property
    def lists_users(self) -> bool:
        return bool(self.kind) or self.all_groups

    @property
    def school_classes(self) -> list[str]:
        return [self.item_id] if self.kind == presentation.SCHOOL_CLASS_KIND else []

    @property
    def work_groups(self) -> list[str]:
        return [self.item_id] if self.kind == presentation.WORK_GROUP_KIND else []

    @property
    def value(self) -> str:
        """The control's value, and the ``group`` of the pushed URL."""
        if self.kind:
            return f"{self.kind}:{self.item_id}"
        return presentation.ALL_GROUPS if self.all_groups else ""


@dataclass(frozen=True)
class _Listing:
    """One request's view of a school, and what it is allowed to skip.

    The handler is left with reading the request and rendering the answer; the
    three reads behind a listing are their own thing, and they need most of the
    same arguments, so they travel together rather than as a parameter list.
    """

    users: UsersPersistencePort
    schools: SchoolsPersistencePort
    school_classes: SchoolClassesPersistencePort
    work_groups: WorkGroupsPersistencePort
    permissions: PermissionsPort
    actor: str
    school: str
    lang: str
    # A deep link can outlive its school. Nothing is read for one the domain no
    # longer has (the file adapter raises on an unknown id).
    known_school: bool
    # htmx keeps only #results-region of the response, so the filter control it
    # would discard is not built.
    results_only: bool

    async def group_sections(self, selection: _GroupSelection) -> list[presentation.OptionGroup]:
        if not self.known_school:
            logger.debug(
                "Requested a school the actor cannot filter by; rendering it without group filters.",
                actor_id=self.actor,
                school=self.school,
            )
            return []
        if self.results_only:
            return []
        return await _group_sections(
            self.school_classes,
            self.work_groups,
            self.permissions,
            self.users,
            self.actor,
            self.school,
            self.lang,
            selected=selection.value if selection.kind else "",
        )

    def users_of(self, selection: _GroupSelection) -> Awaitable[presentation.UserListData]:
        return business_logic.get_users(
            self.users,
            self.schools,
            self.permissions,
            self.actor,
            UsersGetRequest(
                school=self.school,
                school_classes=selection.school_classes,
                work_groups=selection.work_groups,
            ),
            self.lang,
        )

    async def holds(self, selection: _GroupSelection, data: presentation.UserListData) -> bool:
        """Whether the school still holds the selected group.

        A deep link outlives the group it names, and for a moment after a school
        change the results request still carries the previous school's
        selection. A group that listed somebody plainly holds, so only an empty
        result has to ask - and that read is the same group the listing just
        fetched for its members. Asked by name, so it is one lookup when this
        request builds no control, and nothing at all when it does - the
        whole-school read the control needs already answers it.
        """
        if not self.known_school:
            return False
        if data.users:
            return True
        names = [selection.item_id]
        if selection.kind == presentation.SCHOOL_CLASS_KIND:
            return bool(await self.school_classes.get_school_classes_by_name(self.school, names))
        return bool(await self.work_groups.get_work_groups_by_name(self.school, names))


async def _resolve_listing(
    listing: _Listing, selection: _GroupSelection
) -> tuple[list[presentation.OptionGroup], presentation.UserListData | None, _GroupSelection]:
    """The filter control, the table's data and the selection that survived.

    None of the three reads needs another's result, and each is a read of its
    own, so the page cost their sum while they ran in turn. Where they read the
    same thing the request caches collapse it.
    """
    if not selection.lists_users:
        return await listing.group_sections(selection), None, selection
    # Started first so it runs alongside the listing; the listing is awaited
    # first because whether the group holds is read off what it returned.
    sections = asyncio.create_task(listing.group_sections(selection))
    try:
        data = await listing.users_of(selection)
        held = not selection.kind or await listing.holds(selection, data)
    except BaseException:
        await _abandon(sections)
        raise
    if held:
        return await sections, data, selection
    logger.debug(
        "Dropped a group filter the selected school does not have.",
        school=listing.school,
        group_kind=selection.kind,
        group_id=selection.item_id,
    )
    # Whatever the speculative read returned answers a question nobody
    # asked, so it goes with the selection.
    return await sections, None, _GroupSelection()


async def _abandon(task: asyncio.Task[list[presentation.OptionGroup]]) -> None:
    """Cancel ``task`` and wait until it is done.

    Left running, it would go on using the request's Kelvin session after the
    scope closed it, and fail unawaited - logged by asyncio later, without the
    request's correlation id, as a second traceback pointing away from the
    error that ended the request. Cancelling a task that already failed marks
    its error as seen, so that one is not logged either.
    """
    task.cancel()
    await asyncio.wait([task])


def _list_view(
    data: presentation.UserListData | None,
    lang: str,
    known_school: bool,
) -> presentation.UserListView:
    """The table, or the reason there is not one yet.

    An empty table reads as an answer, and nothing was asked until a school and
    a group have been picked - so say which of the two is missing.
    """
    if data is not None:
        return presentation.build_user_list(data, lang)
    if known_school:
        hint = _("Select a class or work group to list its users.", lang=lang)
    else:
        # A link to a school that is gone has no groups to offer.
        hint = _("Select a school and a group to list users.", lang=lang)
    return presentation.empty_user_list_view(lang, hint=hint)


def _push_url(school: str | None, selected_group: str) -> str:
    """The canonical, shareable URL for a filter state.

    Set unconditionally as ``HX-Push-Url``, which htmx prefers over the request
    URL - that is what keeps an empty group selection out of the address bar.
    """
    params = {"school": school} if school else {}
    if selected_group:
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
    school_classes, work_groups = await business_logic.get_group_filters(
        school_classes_adapter,
        work_groups_adapter,
        permissions_adapter,
        users_adapter,
        actor,
        school,
        lang,
    )
    return presentation.build_group_options(
        school_classes,
        work_groups,
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
        # A fresh school starts with nothing selected, so nothing is listed until
        # the user says what they want to see.
        selected_group="",
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
        users_adapter, permissions_adapter, actor, selected_ids(form), lang
    )
    if data.request_error is not None:
        # Nothing was resolved, so a dialog would have nothing to state.
        message, variant = presentation.build_password_reset_summary(
            presentation.PasswordResetResultData(outcomes=[], request_error=data.request_error),
            lang,
        )
        response = render_static(request, "fragments/toast.html", message=message, variant=variant)
        response.headers["HX-Retarget"] = "#toast-region"
        response.headers["HX-Reswap"] = "beforeend"
        return response
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
