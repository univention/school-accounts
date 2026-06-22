# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
import json

import pytest
from guardian_authz_client.errors import GuardianAuthzClientError, HTTPStatusError
from guardian_authz_client.models import (
    Actor,
    Context,
    GetPermissionsResult,
    GuardianObject,
    Role,
    TargetPermission,
)
from guardian_authz_client.models import (
    Permission as ClientPermission,
)

from user_management_bff.adapters.permissions import (
    FilePermissionsAdapter,
    FilePermissionsAdapterSettings,
    GuardianPermissionsAdapter,
    GuardianPermissionsAdapterSettings,
    ucsschool_roles_to_guardian_roles,
)
from user_management_bff.constants import APP_NAME, NAMESPACE_NAME
from user_management_bff.errors import PermissionsError
from user_management_bff.models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UserAttributes,
)


@pytest.mark.parametrize(
    "role_strings,expected",
    [
        ([], []),
        (["a:b:c"], []),
        (
            ["a:school:c"],
            [
                Role(
                    app_name=APP_NAME,
                    namespace_name=NAMESPACE_NAME,
                    name="a",
                    context=Context(app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="c"),
                )
            ],
        ),
        (
            ["", "a:school:c", "d:e:f"],
            [
                Role(
                    app_name=APP_NAME,
                    namespace_name=NAMESPACE_NAME,
                    name="a",
                    context=Context(app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="c"),
                )
            ],
        ),
    ],
)
def test_ucsschool_roles_to_guardian_roles(role_strings, expected):
    assert ucsschool_roles_to_guardian_roles(role_strings) == expected


class TestGuardianPermissionsAdapter:
    @pytest.fixture
    def adapter(self) -> GuardianPermissionsAdapter:
        return GuardianPermissionsAdapter()

    @pytest.fixture
    def settings(self) -> GuardianPermissionsAdapterSettings:
        return GuardianPermissionsAdapterSettings(
            guardian_url="GUARDIAN_URL",
            oauth2_well_known_url="OAUTH2_URL",
            client_id="CLIENT_ID",
            client_secret="CLIENT_SECRET",
            request_timeout=10,
        )

    @pytest.fixture
    def oauth2_settings(self):
        return {"token_endpoint": "TOKEN_ENDPOINT"}

    @pytest.fixture
    def configured_adapter(self, adapter, settings, oauth2_settings):
        adapter._settings = settings
        adapter._oauth2_settings = oauth2_settings
        return adapter

    @pytest.fixture
    def user(self):
        return User(
            id="ID",
            attributes=UserAttributes(
                last_name="LN",
                first_name="FN",
                disabled=False,
                username="USERNAME",
                schools=[],
                roles=[],
                school_classes={},
                work_groups={},
            ),
        )

    def test_init_state(self, adapter):
        assert adapter._settings is None
        assert adapter._client is None
        assert adapter._oauth2_settings == {}

    @pytest.mark.parametrize(
        "attr,expected",
        [
            (1, 1),
            (True, True),
            ("a", "a"),
            (1.1, 1.1),
            (datetime.datetime(2000, 1, 1), "2000-01-01 00:00:00"),
        ],
    )
    def test__sanitize_attr(self, adapter, attr, expected):
        assert adapter._sanitize_attr(attr) == expected

    @pytest.mark.parametrize(
        "user_data",
        [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "Dev",
                    "last_name": "User",
                    "roles": ["teacher:school:school1"],
                    "school_classes": {"school1": ["1a", "2b"]},
                    "work_groups": {},
                    "schools": ["school1"],
                    "username": "dev",
                    "password": None,
                    "email": None,
                    "birthday": None,
                    "expiration_date": None,
                },
                "id": "dev",
            },
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname3",
                    "last_name": "lastname3",
                    "roles": ["teacher:school:test_school2", "student:school:test_school3"],
                    "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                    "work_groups": {},
                    "schools": ["test_school2", "test_school3"],
                    "username": "firstname3.lastname3",
                    "password": None,
                    "email": None,
                    "birthday": None,
                    "expiration_date": None,
                },
                "id": "test_user3",
            },
        ],
    )
    def test__user_to_actor(self, adapter, user_data):
        user = User(id=user_data["id"], attributes=UserAttributes(**user_data["attributes"]))
        expected_roles = [
            Role(
                app_name=APP_NAME,
                namespace_name=NAMESPACE_NAME,
                name=role_parts[0],
                context=Context(app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name=role_parts[2]),
            )
            for role_str in user_data["attributes"]["roles"]
            if (role_parts := role_str.split(":"))
        ]
        expected = Actor(id=user_data["id"], roles=expected_roles, attributes=user_data["attributes"])
        assert adapter._user_to_actor(user) == expected

    @pytest.mark.parametrize(
        "target_obj,expected",
        [
            (None, None),
            (
                TargetObject(id="ID", attributes={}, type=TargetObjectType.SCHOOL),
                GuardianObject(
                    id="ID",
                    attributes={},
                    roles=[
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="school",
                            context=Context(app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="ID"),
                        )
                    ],
                ),
            ),
            (
                TargetObject(id="ID2", attributes={"1": 2}, type=TargetObjectType.SCHOOL),
                GuardianObject(
                    id="ID2",
                    attributes={"1": 2},
                    roles=[
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="school",
                            context=Context(
                                app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="ID2"
                            ),
                        )
                    ],
                ),
            ),
            (
                TargetObject(
                    id="ID3",
                    attributes={
                        "roles": ["teacher:school:school1", "student:school:school2"],
                        "schools": ["school1", "school2"],
                    },
                    type=TargetObjectType.USER,
                ),
                GuardianObject(
                    id="ID3",
                    attributes={
                        "roles": ["teacher:school:school1", "student:school:school2"],
                        "schools": ["school1", "school2"],
                    },
                    roles=[
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="teacher",
                            context=Context(
                                app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="school1"
                            ),
                        ),
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="student",
                            context=Context(
                                app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="school2"
                            ),
                        ),
                    ],
                ),
            ),
            (
                TargetObject(
                    id="ID4", attributes={"school": "school1"}, type=TargetObjectType.SCHOOL_CLASS
                ),
                GuardianObject(
                    id="ID4",
                    attributes={"school": "school1"},
                    roles=[
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="school_class",
                            context=Context(
                                app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="school1"
                            ),
                        )
                    ],
                ),
            ),
            (
                TargetObject(
                    id="ID5", attributes={"school": "school1"}, type=TargetObjectType.WORK_GROUP
                ),
                GuardianObject(
                    id="ID5",
                    attributes={"school": "school1"},
                    roles=[
                        Role(
                            app_name=APP_NAME,
                            namespace_name=NAMESPACE_NAME,
                            name="workgroup",
                            context=Context(
                                app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="school1"
                            ),
                        )
                    ],
                ),
            ),
        ],
    )
    def test__target_object_to_guardian_object(self, adapter, target_obj, expected):
        assert adapter._target_object_to_guardian_object(target_obj) == expected

    @pytest.mark.parametrize(
        "result,expected",
        [
            (
                GetPermissionsResult(
                    actor_id="ACTOR_ID",
                    general_permissions=[],
                    target_permissions=[TargetPermission(target_id="ID1", permissions=[])],
                ),
                {"ID1": []},
            ),
            (
                GetPermissionsResult(actor_id="ACTOR_ID", general_permissions=[], target_permissions=[]),
                {},
            ),
            (
                GetPermissionsResult(
                    actor_id="ACTOR_ID",
                    general_permissions=[],
                    target_permissions=[TargetPermission(target_id="ID1", permissions=[])],
                ),
                {"ID1": []},
            ),
            (
                GetPermissionsResult(
                    actor_id="ACTOR_ID",
                    general_permissions=[
                        ClientPermission(app_name="APP", namespace_name="NAMESPACE", name="create-user")
                    ],
                    target_permissions=[
                        TargetPermission(
                            target_id="ID1",
                            permissions=[
                                ClientPermission(
                                    app_name="APP", namespace_name="NAMESPACE", name="create-user"
                                )
                            ],
                        )
                    ],
                ),
                {"ID1": []},
            ),
            (
                GetPermissionsResult(
                    actor_id="ACTOR_ID",
                    general_permissions=[
                        ClientPermission(app_name="APP", namespace_name="NAMESPACE", name="create-user")
                    ],
                    target_permissions=[
                        TargetPermission(
                            target_id="ID1",
                            permissions=[
                                ClientPermission(
                                    app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="create-user"
                                )
                            ],
                        )
                    ],
                ),
                {"ID1": [Permission.create_user]},
            ),
            (
                GetPermissionsResult(
                    actor_id="ACTOR_ID",
                    general_permissions=[
                        ClientPermission(app_name="APP", namespace_name="NAMESPACE", name="create-user")
                    ],
                    target_permissions=[
                        TargetPermission(
                            target_id="ID1",
                            permissions=[
                                ClientPermission(
                                    app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="unknown"
                                )
                            ],
                        )
                    ],
                ),
                {"ID1": []},
            ),
        ],
    )
    def test__permissions_result_to_permissions_dict(self, adapter, result, expected):
        assert adapter._permissions_result_to_permissions_dict(result) == expected

    def test_settings_property(self, adapter, settings):
        with pytest.raises(
            RuntimeError,
            match="The settings should never be accessed before the adapter was configured!",
        ):
            _settings = adapter.settings
        adapter._settings = settings
        assert adapter.settings == settings

    def test_client(self, configured_adapter):
        assert configured_adapter._client is None
        assert configured_adapter.client is not None

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == GuardianPermissionsAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, settings, oauth2_settings, mocker):
        mock = mocker.AsyncMock().func
        mock.return_value = oauth2_settings
        mocker.patch("user_management_bff.adapters.permissions.get_oauth2_settings", mock)
        await adapter.configure(settings)
        mock.assert_called_once()
        assert adapter._settings == settings
        assert adapter._oauth2_settings == oauth2_settings

    @pytest.mark.asyncio
    async def test_get_permissions_err(self, configured_adapter, user, mocker):
        client_mock = mocker.AsyncMock()
        client_mock.get_permissions.side_effect = GuardianAuthzClientError("MESSAGE")
        configured_adapter._client = client_mock
        with pytest.raises(PermissionsError, match="MESSAGE"):
            await configured_adapter.get_permissions(user, [])

    @pytest.mark.asyncio
    async def test_get_permissions_status_err(self, configured_adapter, user, mocker):
        client_mock = mocker.AsyncMock()
        client_mock.get_permissions.side_effect = HTTPStatusError("MESSAGE", 500)
        configured_adapter._client = client_mock
        with pytest.raises(PermissionsError, match="MESSAGE"):
            await configured_adapter.get_permissions(user, [])

    @pytest.mark.asyncio
    async def test_get_permissions(self, configured_adapter, user, mocker):
        client_mock = mocker.AsyncMock()
        client_mock.get_permissions.return_value = GetPermissionsResult(
            actor_id="ID",
            general_permissions=[],
            target_permissions=[
                TargetPermission(
                    target_id="TID",
                    permissions=[
                        ClientPermission(
                            app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name="create-user"
                        )
                    ],
                )
            ],
        )
        configured_adapter._client = client_mock
        result = await configured_adapter.get_permissions(user, [])
        assert result == {"TID": [Permission.create_user]}


class TestFilePermissionsAdapter:
    @pytest.fixture
    def adapter(self):
        return FilePermissionsAdapter()

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == FilePermissionsAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, tmpdir):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FilePermissionsAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({}, []),
            ({"ID": {"school": ["create-user"]}}, [Permission.create_user]),
            ({"ID": {"school": ["create-user", "unknown-permission"]}}, [Permission.create_user]),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_permissions_for_schools(self, adapter, data, expected):
        adapter._data = data
        actor = User(
            id="ID",
            attributes=UserAttributes(
                first_name="Max",
                last_name="Mustermann",
                username="max.muster",
                disabled=False,
                schools=[],
                school_classes={},
                roles=[],
                work_groups={},
            ),
        )
        target1 = Target(old_target=TargetObject(id="ID", type="school", attributes={}), new_target=None)
        result = await adapter.get_permissions(actor, [target1])
        assert result == {target1.old_target.id: expected}

        # same but with new_target
        target2 = Target(old_target=None, new_target=TargetObject(id="ID", type="school", attributes={}))
        result = await adapter.get_permissions(actor, [target2])
        assert result == {target2.new_target.id: expected}
