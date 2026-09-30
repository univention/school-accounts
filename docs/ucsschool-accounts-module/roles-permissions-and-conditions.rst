.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _roles-permissions-and-conditions:

*********************
Roles and permissions
*********************

This section is for administrators
and describes what each role can do in the |UASUMM| app.
The :external+uv-nubus-manual:ref:`Guardian <nubus-authorization>`
makes the authorization decisions,
using a policy bundle that ships with the |UASUMM| app.
For more information about how the Guardian reaches a decision,
see :external+uv-nubus-manual:ref:`nubus-authorization-policies`.

The policy bundle fixes the roles and their permissions.
You can't create roles or change the permissions of a role.

.. _roles-table:

Permissions of each role
========================

The following table shows what a user with each role can do
on other users in the same school:

.. list-table:: Permissions of each role
   :header-rows: 1
   :align: left
   :widths: 22 22 28 28

   * - Role
     - Read user data of
     - Reset passwords of
     - Own password reset by
   * - School administrator (``school_admin``)
     - Every user in their school
     - Every user in their school, except school administrators
     - Nobody
   * - Teacher (``teacher``)
     - Students in their school classes
     - Students in their school classes whose only role is ``student``
     - School administrators
   * - Staff (``staff``)
     - Nobody
     - Nobody
     - School administrators
   * - Student (``student``)
     - Nobody
     - Nobody
     - Teachers of their school classes, school administrators, and legal guardians
   * - Legal guardian
     - Their wards
     - Their wards whose only role is ``student``
     - School administrators

The following rules apply to every role:

* A user can read their own data, unless ``student`` is their only role.
* A user can filter the list view by the schools they're enrolled in
  and by the school classes and work groups they're a member of.
  A school administrator can also filter by every school class and work group in their school.
* Nobody can reset their own password.
* A password reset requires permission for *every* role of the user whose password is reset.
  For example, a teacher can't reset the password of a student who is also a staff member,
  and nobody can reset the password of a user who holds ``school_admin`` in any school.
* A role counts only at the schools where a user holds it,
  and the other user must be enrolled in one of those schools.
* The role ``student`` takes nothing away from a user who also holds another role.

.. _legal-guardian:

Legal guardians
===============

Legal guardianship is a relationship between two users
that UCS\@school records on both of them.
A legal guardian can read the data of their wards because of that relationship alone,
whatever roles or schools either user has.
Resetting the password of a ward also requires that ``student`` is the ward's only role.
To see a ward in the list view,
the legal guardian must be enrolled in the school of the ward.

UCS\@school also gives a legal guardian the role ``legal_guardian``
in the school of their wards.
Because of that role, only school administrators can reset the password of a legal guardian,
and a legal guardian can read their own data.
