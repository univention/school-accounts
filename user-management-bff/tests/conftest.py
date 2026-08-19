# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os
import subprocess
from pathlib import Path

import nest_asyncio
import pytest
from fastapi.testclient import TestClient

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
    from user_management_bff.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def patch_env():
    _environ = os.environ.copy()
    os.environ["USER_MANAGEMENT__CORS__ALLOWED_ORIGINS"] = "*"
    os.environ["USER_MANAGEMENT__ADAPTER__USERS_PERSISTENCE"] = (
        "user_management_bff.adapters.users:FileUsersPersistenceAdapter"
    )
    os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/users.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOLS_PERSISTENCE"] = (
        "user_management_bff.adapters.schools:FileSchoolsPersistenceAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__AUTHENTICATION"] = (
        "user_management_bff.adapters.authentication:AlwaysAuthenticatedAdapter"
    )
    os.environ["ALWAYS_AUTHENTICATED_ADAPTER__ACTOR_ID"] = "dev"
    os.environ["USER_MANAGEMENT__ADAPTER__SESSION_STORE"] = (
        "user_management_bff.adapters.session_store:InMemorySessionStoreAdapter"
    )
    os.environ["FILE_SCHOOLS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/schools.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__PERMISSIONS"] = (
        "user_management_bff.adapters.permissions:FilePermissionsAdapter"
    )
    os.environ["FILE_PERMISSIONS_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/permissions.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOL_CLASSES_PERSISTENCE"] = (
        "user_management_bff.adapters.school_classes:FileSchoolClassesPersistenceAdapter"
    )
    os.environ["FILE_SCHOOL_CLASSES_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/school_classes.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__WORK_GROUPS_PERSISTENCE"] = (
        "user_management_bff.adapters.work_groups:FileWorkGroupsPersistenceAdapter"
    )
    os.environ["FILE_WORK_GROUPS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/work_groups.json"
    )
    yield
    os.environ.clear()
    os.environ.update(_environ)
