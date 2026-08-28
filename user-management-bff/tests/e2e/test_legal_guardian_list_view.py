# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# The legal guardian route is decided by `P.id in R.attr.old.legal_guardians`.
# Everywhere else that attribute is written by hand - the policy suite spells it
# into its YAML fixtures, and test_cerbos_permissions_adapter builds it in
# `_user_target()` - so both sides of the seam assert the same assumption, and a
# directory service that delivers something else would not fail a single test.
#
# These tests take the attribute from Kelvin instead, and drive
# `business_logic` rather than `CerbosPermissionsAdapter` directly, so the
# school-filter half of the list view is covered as well: a guardian who cannot
# use their ward's school as a filter never reaches the ward, whatever the user
# policy says.
#
# The end-to-end list view itself - `business_logic.get_users()` with the empty
# group filters `routes.py` sends for the default view - is not covered here.
# `KelvinUsersPersistenceAdapter.get_users()` treats only `None` as "no group
# filter" and returns nothing for an empty list, which drops the list view for
# every role, not just guardians. The test was removed until that adapter defect
# is fixed; put it back with the fix.

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from user_management_bff import business_logic
from user_management_bff.models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectType,
)

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any, Callable

    from ucsschool.kelvin.client import User as KelvinUser

    from user_management_bff.adapters.permissions import CerbosPermissionsAdapter

    from .conftest import KelvinPorts

# Imported by dev/tests/import_users.csv, linked by the `udm ... --set
# ucsschoolLegalGuardian` call in dev/tests/integration_tests.cfg.
SCHOOL = "school1"
GUARDIAN = "petra.parent"
WARD = "max.student"
LANG = "en"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_kelvin_delivers_the_imported_guardianship(kelvin_ports: KelvinPorts):
    """The directory service, not a fixture, is the source of the guardianship."""
    guardian = await kelvin_ports.users.get_user(GUARDIAN)
    ward = await kelvin_ports.users.get_user(WARD)

    # What the `guardian_of_ward` policy variable keys on. A Kelvin that omits
    # the attribute yields [] here rather than an error, and every guardian is
    # then denied silently - which is what this assertion is for.
    assert ward.attributes.legal_guardians == [GUARDIAN]
    assert guardian.attributes.legal_wards == [WARD]
    # The role the directory service gives a guardian in their ward's school.
    assert f"legal_guardian:school:{SCHOOL}" in guardian.attributes.roles
    # Without this enrolment the guardian has no school to filter by.
    assert SCHOOL in guardian.attributes.schools


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_legal_guardian_can_filter_by_their_wards_school(
    kelvin_ports: KelvinPorts, cerbos_adapter: CerbosPermissionsAdapter
):
    """`school_resource` keeps only schools the actor is enrolled in."""
    schools = await business_logic.get_schools(
        kelvin_ports.schools, cerbos_adapter, kelvin_ports.users, GUARDIAN, LANG
    )
    assert SCHOOL in [school.id for school in schools.schools]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_a_guardianship_created_through_kelvin_reaches_the_policy(
    kelvin_ports: KelvinPorts,
    cerbos_adapter: CerbosPermissionsAdapter,
    kelvin_user_factory: Callable[..., Coroutine[Any, Any, KelvinUser]],
):
    """The same route for a pair Kelvin creates now, not one the image shipped.

    Kelvin accepts `legal_guardians` only on a student and `legal_wards` only on
    a legal guardian, so this is also the check that the two roles the policy
    assumes are the two roles the API actually pairs.
    """
    guardian = await kelvin_user_factory(school=SCHOOL, schools=[SCHOOL], roles=["legal_guardian"])
    ward = await kelvin_user_factory(
        school=SCHOOL,
        schools=[SCHOOL],
        roles=["student"],
        school_classes={SCHOOL: ["1a"]},
        legal_guardians=[guardian.name],
    )

    stored_ward = await kelvin_ports.users.get_user(ward.name)
    assert stored_ward.attributes.legal_guardians == [guardian.name]

    actor = await kelvin_ports.users.get_user(guardian.name)
    # The same Target `business_logic.get_users()` builds, but with attributes
    # that came back from Kelvin rather than ones written here.
    target_object = TargetObject(
        id=stored_ward.id,
        type=TargetObjectType.USER,
        attributes=stored_ward.attributes.model_dump(),
    )
    permissions = await cerbos_adapter.get_permissions(
        actor, [Target(old_target=target_object, new_target=target_object)]
    )
    assert {Permission.read_first_name, Permission.write_password} <= set(permissions[stored_ward.id])
