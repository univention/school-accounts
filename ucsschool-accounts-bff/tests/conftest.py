# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os
import subprocess
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import nest_asyncio
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from ucsschool_accounts_bff.adapters.users import FileUsersPersistenceAdapter
from ucsschool_accounts_bff.errors import PasswordResetRejectedError

nest_asyncio.apply()


def pytest_configure(config: pytest.Config):
    # Compile gettext .po -> .mo so translation tests run against the real
    # catalogs. The .mo files are git-ignored and otherwise only compiled by
    # CI/translate tasks, so without this a local pytest run falls back to the
    # untranslated strings (e.g. test_translation_smoke_test[de-Klassen]).
    script = Path(__file__).parent.parent / "scripts" / "translate.sh"
    subprocess.run([str(script)], check=True)


@pytest.fixture(scope="session")
def test_client():
    from ucsschool_accounts_bff import main

    # Starting the app configures loguru process-wide, which would otherwise decide for
    # every later test in the session what its own log records look like.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(main, "configure_logger", AsyncMock())
        with TestClient(main.app) as client:
            yield client


@pytest.fixture(scope="session", autouse=True)
def patch_env():
    _environ = os.environ.copy()
    os.environ["UCSSCHOOL_ACCOUNTS__CORS__ALLOWED_ORIGINS"] = "*"
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__USERS_PERSISTENCE"] = (
        "ucsschool_accounts_bff.adapters.users:FileUsersPersistenceAdapter"
    )
    os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/users.json"
    )
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__SCHOOLS_PERSISTENCE"] = (
        "ucsschool_accounts_bff.adapters.schools:FileSchoolsPersistenceAdapter"
    )
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__AUTHENTICATION"] = (
        "ucsschool_accounts_bff.adapters.authentication:AlwaysAuthenticatedAdapter"
    )
    os.environ["ALWAYS_AUTHENTICATED_ADAPTER__ACTOR_ID"] = "dev"
    os.environ["FILE_SCHOOLS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/schools.json"
    )
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__PERMISSIONS"] = (
        "ucsschool_accounts_bff.adapters.permissions:FilePermissionsAdapter"
    )
    os.environ["FILE_PERMISSIONS_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/permissions.json"
    )
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__SCHOOL_CLASSES_PERSISTENCE"] = (
        "ucsschool_accounts_bff.adapters.school_classes:FileSchoolClassesPersistenceAdapter"
    )
    os.environ["FILE_SCHOOL_CLASSES_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/school_classes.json"
    )
    os.environ["UCSSCHOOL_ACCOUNTS__ADAPTER__WORK_GROUPS_PERSISTENCE"] = (
        "ucsschool_accounts_bff.adapters.work_groups:FileWorkGroupsPersistenceAdapter"
    )
    os.environ["FILE_WORK_GROUPS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/work_groups.json"
    )
    yield
    os.environ.clear()
    os.environ.update(_environ)


@pytest.fixture
def patch_set_password(mocker: MockerFixture) -> Callable[[dict[str, Exception]], MagicMock]:
    """Replace ``set_password`` with a double that writes nothing and fails by id.

    The mapping is target id -> the error Kelvin would raise for it; any id not in
    it succeeds, so ``patch_set_password({})`` is the all-succeed case. Nothing is
    written either way: the users port points at the shared ``tests/data/users.json``
    fixture, and the real write is covered in ``tests/adapters/test_users.py``.
    """

    def _install(failures: dict[str, Exception]) -> MagicMock:
        async def _set_password(identifier: str, _password: str, _change: bool = False) -> None:
            error = failures.get(identifier)
            if error is not None:
                raise error

        return mocker.patch.object(
            FileUsersPersistenceAdapter, "set_password", side_effect=_set_password
        )

    return _install


@pytest.fixture
def rejecting_set_password(
    mocker: MockerFixture,
) -> Callable[[str | Callable[[str], str]], MagicMock]:
    """Patch ``set_password`` so that *every* attempt is rejected.

    Failing alike is what tells the UI the password itself is at fault rather than
    any one account, so it gets its own fixture. Pass a callable when the reason
    names the user -- that is the case that must *not* be read as password-level.
    """

    def _install(reason: str | Callable[[str], str]) -> MagicMock:
        async def _set_password(identifier: str, _password: str, _change: bool = False) -> None:
            message = reason(identifier) if callable(reason) else reason
            raise PasswordResetRejectedError(identifier=identifier, message=message)

        return mocker.patch.object(
            FileUsersPersistenceAdapter, "set_password", side_effect=_set_password
        )

    return _install
