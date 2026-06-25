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

from user_management_bff import business_logic
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
    EditConfigRepresentationPort,
    ListConfigRepresentationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolClassesRepresentationPort,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UsersPersistencePort,
    UsersRepresentationPort,
    WorkGroupsPersistencePort,
    WorkGroupsRepresentationPort,
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
        schools_repr=await ADAPTER_REGISTRY(SchoolsRepresentationPort),
        school_classes_repr=await ADAPTER_REGISTRY(SchoolClassesRepresentationPort),
        work_groups_repr=await ADAPTER_REGISTRY(WorkGroupsRepresentationPort),
        list_config_repr=await ADAPTER_REGISTRY(ListConfigRepresentationPort),
        add_config_repr=await ADAPTER_REGISTRY(AddConfigRepresentationPort),
        edit_config_repr=await ADAPTER_REGISTRY(EditConfigRepresentationPort),
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
# List column config
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_list_config_representation(ports, lang):
    config = ports.list_config_repr.list_config_representation(lang)
    assert [column.attribute for column in config.columns] == [
        "last_name",
        "first_name",
        "username",
        "roles",
        "classes",
        "work_groups",
        "schools",
        "activated",
    ]
    assert config.columns[0].label == _("Last name", lang=lang)


# ---------------------------------------------------------------------------
# get_users
# ---------------------------------------------------------------------------
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
    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.users_repr,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=[], work_groups=[]),
        "en",
    )
    assert {user.id for user in result.users} == expected_ids


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
async def test_get_users_no_permissions(_permissions_mock, ports):
    # Users for whom the actor holds no permissions are omitted entirely.
    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.users_repr,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school="test_school1", school_classes=[], work_groups=[]),
        "en",
    )
    assert result.users == []


# ---------------------------------------------------------------------------
# get_schools / get_school_classes / get_work_groups
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_schools(ports):
    result = await business_logic.get_schools(
        ports.schools, ports.schools_repr, ports.permissions, ports.users, ACTOR_ID, "en"
    )
    assert [school.value for school in result.schools] == [
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
        ports.school_classes_repr,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(sc.value, sc.label) for sc in result.school_classes] == [("1a", "1a"), ("2b", "2b")]


@pytest.mark.asyncio
async def test_get_work_groups(ports):
    result = await business_logic.get_work_groups(
        ports.work_groups,
        ports.work_groups_repr,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(wg.value, wg.label) for wg in result.work_groups] == [("w1a", "w1a"), ("w2b", "w2b")]


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


@pytest.mark.asyncio
async def test_create_user(ports, users_json_path):
    result = await business_logic.create_user(
        ports.users, ports.users_repr, ports.users, ports.permissions, ACTOR_ID, _create_request(), "en"
    )
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
        await business_logic.create_user(
            ports.users,
            ports.users_repr,
            ports.users,
            ports.permissions,
            ACTOR_ID,
            _create_request(),
            "en",
        )


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_create_user_permissions_error(_permissions_mock, ports, lang, users_json_path):
    with pytest.raises(PermissionsError) as exc_info:
        await business_logic.create_user(
            ports.users,
            ports.users_repr,
            ports.users,
            ports.permissions,
            ACTOR_ID,
            _create_request(username="bad_username"),
            lang,
        )
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
        await business_logic.delete_user(
            ports.users, ports.permissions, ACTOR_ID, "NON_EXISTENT", "en"
        )
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
@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_patch_user_wrong_school(ports, lang):
    with pytest.raises(OperationNotSupportedError) as exc_info:
        await business_logic.patch_user(
            ports.users,
            ports.users_repr,
            ports.permissions,
            ACTOR_ID,
            UserPatchRequest(
                identifier="test_user1", school="NON_EXISTENT", attributes=UserPatchAttributes()
            ),
            lang,
        )
    assert exc_info.value.message == _(
        "Cannot update user 'test_user1' in school 'NON_EXISTENT'.", lang=lang
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_patch_user_not_found(ports, lang):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await business_logic.patch_user(
            ports.users,
            ports.users_repr,
            ports.permissions,
            ACTOR_ID,
            UserPatchRequest(
                identifier="NON_EXISTENT", school="school1", attributes=UserPatchAttributes()
            ),
            lang,
        )
    assert exc_info.value.identifier == "NON_EXISTENT"


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_patch_user_not_allowed(_permissions_mock, ports, lang):
    with pytest.raises(PermissionsError) as exc_info:
        await business_logic.patch_user(
            ports.users,
            ports.users_repr,
            ports.permissions,
            ACTOR_ID,
            UserPatchRequest(
                identifier="test_user1",
                school="test_school1",
                attributes=UserPatchAttributes(first_name="John"),
            ),
            lang,
        )
    assert exc_info.value.message == _("You do not have the permission to edit this user.", lang=lang)
    assert exc_info.value.missing_permissions == ["write-first_name"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch_dict",
    [{}, {"first_name": "John"}, {"first_name": "John", "username": "jon.doe"}, {"activated": False}],
)
async def test_patch_user(ports, patch_dict):
    result = await business_logic.patch_user(
        ports.users,
        ports.users_repr,
        ports.permissions,
        ACTOR_ID,
        UserPatchRequest(
            identifier="test_user1",
            school="test_school1",
            attributes=UserPatchAttributes(**patch_dict),
        ),
        "en",
    )
    expected = {
        "activated": True,
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "firstname.lastname",
    }
    expected.update(patch_dict)
    assert result.user.attributes.first_name.value == expected["first_name"]
    assert result.user.attributes.last_name.value == expected["last_name"]
    assert result.user.attributes.username.value == expected["username"]
    assert result.user.attributes.activated.value == expected["activated"]
    assert result.user.attributes.classes.value == ["test_school1:1a", "test_school1:2b"]


@pytest.mark.asyncio
async def test_patch_user_school_classes(ports):
    result = await business_logic.patch_user(
        ports.users,
        ports.users_repr,
        ports.permissions,
        ACTOR_ID,
        UserPatchRequest(
            identifier="test_user3",
            school="test_school2",
            attributes=UserPatchAttributes(school_classes=["1a"]),
        ),
        "en",
    )
    assert result.user.attributes.classes.value == [
        "test_school1:1a",
        "test_school1:2b",
        "test_school2:1a",
    ]


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
    result = await business_logic.patch_user(
        ports.users,
        ports.users_repr,
        ports.permissions,
        ACTOR_ID,
        UserPatchRequest(
            identifier="dev", school="school1", attributes=UserPatchAttributes(**patch_dict)
        ),
        "en",
    )
    # Roles are intentionally not updated by the persistence layer.
    assert result.user.attributes.roles.value == ["teacher:school:school1"]


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
# get_user_edit_config
# ---------------------------------------------------------------------------
async def _edit_config(ports, *, user_id, school, lang="en"):
    return await business_logic.get_user_edit_config(
        ports.users,
        ports.users_repr,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.edit_config_repr,
        ports.permissions,
        ACTOR_ID,
        user_id,
        school,
        lang,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_user_edit_config(ports, lang):
    config = await _edit_config(ports, user_id="user3", school="school1", lang=lang)
    assert config.id == "user3"
    assert config.user["first_name"] == "Kim"
    assert config.user["last_name"] == "Klein"
    assert config.user["school"] == "school1"


@pytest.mark.asyncio
async def test_get_user_edit_config_non_existing_user(ports):
    with pytest.raises(ObjectNotFoundError):
        await _edit_config(ports, user_id="NON_EXISTING", school="test_school1")


@pytest.mark.asyncio
async def test_get_user_edit_config_wrong_school(ports):
    with pytest.raises(ObjectNotFoundError):
        await _edit_config(ports, user_id="test_user1", school="school1")


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_user_edit_config_school_doesnt_exist(ports, lang):
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await _edit_config(ports, user_id="test_user1", school="fake_school", lang=lang)
    assert exc_info.value.identifier == "fake_school"
