# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Integration tests for the business logic.

These call ``business_logic.*`` directly using the real file-based adapters
obtained from the configured ``ADAPTER_REGISTRY`` (the registry is configured by
the app startup that the session-scoped ``test_client`` fixture triggers). They
replace the former JSON-route tests removed with the JSON API; the assertions
mirror those tests but against the returned representation objects / raised
exceptions instead of HTTP responses.
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio
from pydantic import ValidationError

from user_management_bff import business_logic, presentation
from user_management_bff.adapter_registry import ADAPTER_REGISTRY
from user_management_bff.adapters.permissions import FilePermissionsAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.api_models import UserCreateRequest
from user_management_bff.business_logic import create_user, get_schools, user_create_request_to_target
from user_management_bff.errors import (
    CreationError,
    NoSchoolUserError,
    ObjectNotFoundError,
    OperationNotSupportedError,
    PermissionsError,
)
from user_management_bff.lang import _
from user_management_bff.models import (
    Permission,
    Role,
    Target,
    TargetObject,
    TargetObjectType,
    UserPatchAttributes,
    UserPatchRequest,
    UsersGetRequest,
)
from user_management_bff.ports import (
    AddConfigRepresentationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    UsersRepresentationPort,
    WorkGroupsPersistencePort,
)

# The actor id supplied by AlwaysAuthenticatedAdapter in the test environment.
ACTOR_ID = "dev"


async def _get_ports() -> SimpleNamespace:
    """Fetch the configured file-based adapters from the registry."""
    return SimpleNamespace(
        users=await ADAPTER_REGISTRY(UsersPersistencePort),
        schools=await ADAPTER_REGISTRY(SchoolsPersistencePort),
        school_classes=await ADAPTER_REGISTRY(SchoolClassesPersistencePort),
        work_groups=await ADAPTER_REGISTRY(WorkGroupsPersistencePort),
        users_repr=await ADAPTER_REGISTRY(UsersRepresentationPort),
        add_config_repr=await ADAPTER_REGISTRY(AddConfigRepresentationPort),
        permissions=await ADAPTER_REGISTRY(PermissionsPort),
    )


@pytest_asyncio.fixture
async def ports(test_client):
    # `test_client` triggers app startup, which configures the registry.
    return await _get_ports()


# ---------------------------------------------------------------------------
# Pure helpers / actor resolution
# ---------------------------------------------------------------------------
@pytest.fixture
def users_get_not_found_mock(mocker):
    users_get_mock = mocker.AsyncMock()
    users_get_mock.get_user.side_effect = ObjectNotFoundError(identifier="USER")
    return users_get_mock


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_schools_actor_not_found(mocker, users_get_not_found_mock, lang):
    user = "USER"
    with pytest.raises(
        NoSchoolUserError,
        match=_(f"The logged in user '{user}' is not a valid UCS@school user.", lang=lang),
    ) as exc_info:
        await get_schools(
            mocker.AsyncMock(),
            mocker.AsyncMock(),
            users_get_not_found_mock,
            "USER",
            lang,
        )
    assert exc_info.value.identifier == "USER"


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_create_user_actor_not_found(mocker, users_get_not_found_mock, lang):
    user = "USER"
    with pytest.raises(
        NoSchoolUserError,
        match=_(f"The logged in user '{user}' is not a valid UCS@school user.", lang=lang),
    ) as exc_info:
        await create_user(
            mocker.MagicMock(),
            mocker.MagicMock(),
            users_get_not_found_mock,
            mocker.MagicMock(),
            "USER",
            mocker.MagicMock(),
            lang,
        )
    assert exc_info.value.identifier == "USER"


def test_user_create_request_to_target():
    user = UserCreateRequest(
        last_name="Mustermann",
        first_name="Max",
        username="max.mustermann",
        password="univention",
        school="school1",
        school_classes=["1a"],
        work_groups=["w1a"],
        roles=[Role.TEACHER],
    )
    expected = Target(
        old_target=None,
        new_target=TargetObject(
            id="max.mustermann",
            type=TargetObjectType.USER,
            attributes=dict(
                last_name="Mustermann",
                first_name="Max",
                username="max.mustermann",
                password="univention",
                schools=["school1"],
                school_classes={"school1": ["1a"]},
                work_groups={"school1": ["w1a"]},
                roles=["teacher:school:school1"],
                activated=True,
            ),
        ),
    )
    assert user_create_request_to_target(user) == expected


# ---------------------------------------------------------------------------
# get_users
# ---------------------------------------------------------------------------
async def _get_users(ports, school, *, lang="en"):
    return await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=[], work_groups=[]),
        lang,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "school,expected_ids",
    [
        ("NON_EXISTENT", set()),
        ("test_school1", {"test_user1", "test_user4"}),
        ("test_school2", {"test_user2", "test_user3"}),
    ],
)
async def test_get_users(ports, school, expected_ids):
    result = await _get_users(ports, school)
    assert {user.id for user in result.users} == expected_ids


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
async def test_get_users_no_permissions(_permissions_mock, ports):
    # Users for whom the actor holds no permissions are omitted from the view.
    result = await _get_users(ports, "test_school1")
    assert presentation.build_user_list(result, "en", "test_school1").rows == []


# ---------------------------------------------------------------------------
# get_schools / get_school_classes / get_work_groups
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_schools(ports):
    result = await business_logic.get_schools(
        ports.schools, ports.permissions, ports.users, ACTOR_ID, "en"
    )
    assert [school.id for school in result.schools] == [
        "school1",
        "school2",
        "school3",
        "school4",
        "test_school1",
        "test_school2",
        "test_school3",
    ]


@pytest.mark.asyncio
async def test_get_school_classes(ports):
    result = await business_logic.get_school_classes(
        ports.school_classes,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(sc.id, sc.display_name) for sc in result] == [("1a", "1a"), ("2b", "2b")]


@pytest.mark.asyncio
async def test_get_work_groups(ports):
    result = await business_logic.get_work_groups(
        ports.work_groups,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(wg.id, wg.display_name) for wg in result] == [("w1a", "w1a"), ("w2b", "w2b")]


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------
def _create_request(**overrides) -> UserCreateRequest:
    data = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "username",
        "roles": ["teacher"],
        "school": "test_school1",
        "school_classes": ["1a", "2b"],
        "password": "password",
    }
    data.update(overrides)
    return UserCreateRequest(**data)


async def _create_user(ports, request, *, lang="en"):
    return await business_logic.create_user(
        ports.users, ports.users_repr, ports.users, ports.permissions, ACTOR_ID, request, lang
    )


@pytest.mark.asyncio
async def test_create_user(ports, users_json_path):
    result = await _create_user(ports, _create_request())
    assert result.user.id == "username"
    assert result.user.attributes.classes.value == ["test_school1:1a", "test_school1:2b"]
    assert result.user.attributes.roles.value == ["teacher:school:test_school1"]

    with open(users_json_path, "r") as file:
        users = json.load(file)
    assert users[-1]["id"] == "username"


@pytest.mark.asyncio
@patch.object(FileUsersPersistenceAdapter, "create_user", side_effect=CreationError("error"))
async def test_create_user_creation_error(_create_mock, ports):
    with pytest.raises(CreationError, match="error"):
        await _create_user(ports, _create_request())


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_create_user_permissions_error(_permissions_mock, ports, lang, users_json_path):
    with pytest.raises(PermissionsError) as exc_info:
        await _create_user(ports, _create_request(username="bad_username"), lang=lang)
    assert exc_info.value.message == _("You do not have the permission to create this user.", lang=lang)

    with open(users_json_path, "r") as file:
        users = json.load(file)
    assert all(user["id"] != "bad_username" for user in users)


def test_create_user_classes_validation_error():
    # A student without a school class is rejected at request-model construction.
    # The validator emits the untranslated source message; translating it to the
    # request language is a presentation concern (the error-rendering layer), not
    # the model's job.
    with pytest.raises(ValidationError) as exc_info:
        _create_request(username="bad_username", roles=["student"], school_classes=[])
    assert "A student must be member of at least one school class." in str(exc_info.value)


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_user_non_existent(ports):
    # A non-existent user is treated as a successful deletion (no error).
    assert (
        await business_logic.delete_user(ports.users, ports.permissions, ACTOR_ID, "NON_EXISTENT", "en")
        is None
    )


@pytest.mark.asyncio
async def test_delete_user(ports, users_json_path):
    await business_logic.delete_user(ports.users, ports.permissions, ACTOR_ID, "test_user1", "en")
    with open(users_json_path, "r") as file:
        users = json.load(file)
    assert all(user["id"] != "test_user1" for user in users)


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_delete_user_not_allowed(_permissions_mock, ports, lang):
    with pytest.raises(PermissionsError) as exc_info:
        await business_logic.delete_user(ports.users, ports.permissions, ACTOR_ID, "test_user1", lang)
    assert exc_info.value.message == _("You do not have the permission to edit this user.", lang=lang)


@pytest.mark.asyncio
@patch.object(FileUsersPersistenceAdapter, "delete_user", side_effect=ObjectNotFoundError("ID"))
async def test_delete_user_race_condition(_delete_mock, ports):
    # The user exists at permission-check time but is gone by the time we delete:
    # treated as a successful deletion.
    assert (
        await business_logic.delete_user(ports.users, ports.permissions, ACTOR_ID, "test_user1", "en")
        is None
    )


# ---------------------------------------------------------------------------
# patch_user
# ---------------------------------------------------------------------------
async def _patch_user(ports, request, *, lang="en"):
    return await business_logic.patch_user(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.permissions,
        ACTOR_ID,
        request,
        lang,
    )


@pytest.mark.asyncio
async def test_patch_user_wrong_school(ports):
    with pytest.raises(OperationNotSupportedError) as exc_info:
        await _patch_user(
            ports,
            UserPatchRequest(
                identifier="test_user1", school="NON_EXISTENT", attributes=UserPatchAttributes()
            ),
        )
    assert exc_info.value.message == "Cannot update user 'test_user1' in school 'NON_EXISTENT'."


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_patch_user_not_found(ports, lang):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await _patch_user(
            ports,
            UserPatchRequest(
                identifier="NON_EXISTENT", school="school1", attributes=UserPatchAttributes()
            ),
            lang=lang,
        )
    assert exc_info.value.identifier == "NON_EXISTENT"


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_patch_user_not_allowed(_permissions_mock, ports, lang):
    with pytest.raises(PermissionsError) as exc_info:
        await _patch_user(
            ports,
            UserPatchRequest(
                identifier="test_user1",
                school="test_school1",
                attributes=UserPatchAttributes(first_name="John"),
            ),
            lang=lang,
        )
    assert exc_info.value.message == _("You do not have the permission to edit this user.", lang=lang)
    assert exc_info.value.missing_permissions == ["write-first_name"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch_dict",
    [{}, {"first_name": "John"}, {"first_name": "John", "username": "jon.doe"}, {"activated": False}],
)
async def test_patch_user(ports, patch_dict):
    result = await _patch_user(
        ports,
        UserPatchRequest(
            identifier="test_user1",
            school="test_school1",
            attributes=UserPatchAttributes(**patch_dict),
        ),
    )
    expected = {
        "activated": True,
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "firstname.lastname",
    }
    expected.update(patch_dict)
    assert result.school == "test_school1"
    assert result.user.attributes.first_name == expected["first_name"]
    assert result.user.attributes.last_name == expected["last_name"]
    assert result.user.attributes.username == expected["username"]
    assert (not result.user.attributes.disabled) == expected["activated"]
    assert result.user.attributes.school_classes == {"test_school1": ["1a", "2b"]}


@pytest.mark.asyncio
async def test_patch_user_school_classes(ports):
    result = await _patch_user(
        ports,
        UserPatchRequest(
            identifier="test_user3",
            school="test_school2",
            attributes=UserPatchAttributes(school_classes=["1a"]),
        ),
    )
    assert result.user.attributes.school_classes == {
        "test_school1": ["1a", "2b"],
        "test_school2": ["1a"],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch_dict",
    [
        {"roles": ["student"]},
        {"roles": ["student", "teacher"]},
        {"roles": ["student", "teacher", "administrator", "staff"]},
        {"roles": ["teacher"]},
    ],
)
async def test_patch_user_change_roles(ports, patch_dict):
    result = await _patch_user(
        ports,
        UserPatchRequest(
            identifier="dev", school="school1", attributes=UserPatchAttributes(**patch_dict)
        ),
    )
    # Roles are intentionally not updated by the persistence layer.
    assert result.user.attributes.roles == ["teacher:school:school1"]


# ---------------------------------------------------------------------------
# get_user_add_config
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_user_add_config(ports, lang):
    config = await business_logic.get_user_add_config(
        ports.schools, ports.school_classes, ports.work_groups, ports.add_config_repr, "school1", lang
    )
    assert [page.name for page in config.pages] == ["useradd"]
    assert config.pages[0].label == _("Add user", lang=lang)


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_user_add_config_school_doesnt_exist(ports, lang):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await business_logic.get_user_add_config(
            ports.schools,
            ports.school_classes,
            ports.work_groups,
            ports.add_config_repr,
            "fake_school",
            lang,
        )
    assert exc_info.value.identifier == "fake_school"


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------
async def _get_user(ports, *, user_id, school, lang="en"):
    return await business_logic.get_user(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.permissions,
        ACTOR_ID,
        user_id,
        school,
        lang,
    )


@pytest.mark.asyncio
async def test_get_user(ports):
    data = await _get_user(ports, user_id="user3", school="school1")
    assert data.user.id == "user3"
    assert data.school == "school1"
    # The dev actor holds every write permission on user targets in the fixture.
    assert Permission.write_first_name in data.permissions
    # Display context is fetched for every school the user belongs to.
    assert set(data.school_classes) >= set(data.user.attributes.schools)
    assert any(school.id == "school1" for school in data.schools)


@pytest.mark.asyncio
async def test_get_user_non_existing_user(ports):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await _get_user(ports, user_id="NON_EXISTING", school="school1")
    assert exc_info.value.identifier == "NON_EXISTING"


@pytest.mark.asyncio
async def test_get_user_wrong_school(ports):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await _get_user(ports, user_id="user3", school="school4")
    assert exc_info.value.identifier == "user3:school4"


# ---------------------------------------------------------------------------
# Edge cases / branch behaviour beyond plain line coverage
#
# The file permissions adapter grants permissions per target *type*, so the
# integration tests above cannot exercise per-object permission differences.
# These tests mock get_permissions to return per-id results.
# ---------------------------------------------------------------------------
def _permissions_by_id(mapping: dict[str, list[Permission]]):
    """Build a get_permissions side effect returning ``mapping`` keyed by target id.

    Any target not present in ``mapping`` resolves to an empty permission list.
    """

    def _side_effect(actor, targets):
        return {
            (target.old_target or target.new_target).id: mapping.get(
                (target.old_target or target.new_target).id, []
            )
            for target in targets
        }

    return _side_effect


# get_school_classes / get_work_groups filter out entries the actor
# may not use as a filter (the False side of the use_as_filter check).
@pytest.mark.asyncio
async def test_get_school_classes_filters_by_use_as_filter(ports, mocker):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"1a": [Permission.use_as_filter]}),
    )
    result = await business_logic.get_school_classes(
        ports.school_classes,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    # "2b" is dropped because the actor lacks use_as_filter on it.
    assert [sc.id for sc in result] == ["1a"]


@pytest.mark.asyncio
async def test_get_work_groups_filters_by_use_as_filter(ports, mocker):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"w1a": [Permission.use_as_filter]}),
    )
    result = await business_logic.get_work_groups(
        ports.work_groups,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [wg.id for wg in result] == ["w1a"]


# get_users returns only the users the actor holds a permission for
# (partial visibility, not the all-or-nothing cases above).
@pytest.mark.asyncio
async def test_get_users_partial_visibility(ports, mocker):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.read_first_name]}),
    )
    result = await _get_users(ports, "test_school1")
    # test_school1 also contains test_user4, but the actor has no permission for it,
    # so only test_user1 is rendered into a row.
    view = presentation.build_user_list(result, "en", "test_school1")
    assert {row.id for row in view.rows} == {"test_user1"}


# create_user / patch_user deny on a *missing subset* of permissions
# and report exactly the missing element (exercises required - granted, not
# required - {}).
@pytest.mark.asyncio
async def test_create_user_partial_permissions(ports, mocker):
    granted = [
        Permission.create_user,
        Permission.write_last_name,
        Permission.write_username,
        Permission.write_roles,
        Permission.write_schools,
        Permission.write_school_classes,
        Permission.write_password,
    ]  # everything the default request needs except write-first_name
    mocker.patch.object(FilePermissionsAdapter, "get_permissions", return_value={"username": granted})
    with pytest.raises(PermissionsError) as exc_info:
        await _create_user(ports, _create_request())
    assert exc_info.value.missing_permissions == [Permission.write_first_name]


@pytest.mark.asyncio
async def test_patch_user_partial_permissions(ports, mocker):
    # Two attributes patched, only one write permission granted -> denied,
    # reporting just the missing one.
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_first_name]}),
    )
    with pytest.raises(PermissionsError) as exc_info:
        await _patch_user(
            ports,
            UserPatchRequest(
                identifier="test_user1",
                school="test_school1",
                attributes=UserPatchAttributes(first_name="John", last_name="Doe"),
            ),
        )
    assert exc_info.value.missing_permissions == [Permission.write_last_name]


# the required permission set follows the explicitly-set request fields
# (model_fields_set), incl. the school -> write-schools remap.
@pytest.mark.asyncio
async def test_create_user_required_permissions_follow_set_fields(ports, mocker):
    granted = [
        Permission.create_user,
        Permission.write_first_name,
        Permission.write_last_name,
        Permission.write_username,
        Permission.write_roles,
        Permission.write_schools,
        Permission.write_school_classes,
        Permission.write_password,
    ]  # note: no write-work_groups
    mocker.patch.object(FilePermissionsAdapter, "get_permissions", return_value={"username": granted})

    # Without work_groups set, this exact grant set is sufficient.
    result = await _create_user(ports, _create_request())
    assert result.user.id == "username"

    # Explicitly setting work_groups adds write-work_groups to the requirement.
    with pytest.raises(PermissionsError) as exc_info:
        await _create_user(ports, _create_request(work_groups=["w1a"]))
    assert exc_info.value.missing_permissions == [Permission.write_work_groups]


# user_create_request_to_target maps plural roles / classes / work
# groups and defaults work_groups to an empty per-school list.
def test_user_create_request_to_target_multiple_values():
    request = UserCreateRequest(
        last_name="Doe",
        first_name="Jane",
        username="jane.doe",
        password="pw",
        school="school1",
        school_classes=["1a", "2b"],
        work_groups=["w1a", "w2b"],
        roles=["teacher", "staff"],
    )
    attributes = user_create_request_to_target(request).new_target.attributes
    assert attributes["schools"] == ["school1"]
    assert attributes["roles"] == ["teacher:school:school1", "staff:school:school1"]
    assert attributes["school_classes"] == {"school1": ["1a", "2b"]}
    assert attributes["work_groups"] == {"school1": ["w1a", "w2b"]}


def test_user_create_request_to_target_defaults_empty_work_groups():
    request = UserCreateRequest(
        last_name="Doe",
        first_name="Jane",
        username="jane.doe",
        school="school1",
        school_classes=["1a"],
        roles=["teacher"],
    )
    attributes = user_create_request_to_target(request).new_target.attributes
    assert attributes["work_groups"] == {"school1": []}


# patch_user reactivation (activated=True -> disabled=False) and
# clearing all school classes.
@pytest.mark.asyncio
async def test_patch_user_reactivation(ports):
    await _patch_user(
        ports,
        UserPatchRequest(
            identifier="test_user1",
            school="test_school1",
            attributes=UserPatchAttributes(activated=False),
        ),
    )
    result = await _patch_user(
        ports,
        UserPatchRequest(
            identifier="test_user1",
            school="test_school1",
            attributes=UserPatchAttributes(activated=True),
        ),
    )
    assert result.user.attributes.disabled is False


@pytest.mark.asyncio
async def test_patch_user_clear_school_classes(ports):
    result = await _patch_user(
        ports,
        UserPatchRequest(
            identifier="test_user1",
            school="test_school1",
            attributes=UserPatchAttributes(school_classes=[]),
        ),
    )
    assert result.user.attributes.school_classes == {"test_school1": []}
