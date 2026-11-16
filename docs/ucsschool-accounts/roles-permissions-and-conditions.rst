.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _roles-permissions-and-conditions:

*********************
Roles and permissions
*********************

This section is for administrators
and describes what each role can do in the |UASSA| app.
The *Guardian* authorization engine
makes the authorization decisions,
using a policy bundle that ships with the |UASSA| app.
For more information about how the Guardian reaches a decision,
see :external+uv-nubus-manual:ref:`nubus-authorization-policies`
in :cite:t:`uv-nubus-manual`.

The policy bundle defines the roles and their permissions.
The app doesn't support creating new roles or changing the permissions of a role.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-authorization`
      in :cite:t:`uv-nubus-manual`
      for more information about the *Guardian* authorization engine.

.. _roles-permissions-each-role:

Permissions of each role
========================

The following list shows what actions a user with each role can perform
on other users in the same school.
Each role has an identifier, a technical name used in role values and policies.
For the permissions of legal guardians, see :ref:`legal-guardian`.

.. _roles-permissions-each-role-school-admin:

School administrator
   :Identifier: ``school_admin``
   :Read user data of: Every user in their school
   :Reset password of: Every user in their school, except school administrators
   :Own password reset by: Nobody

.. _roles-permissions-each-role-teacher:

Teacher
   :Identifier: ``teacher``
   :Read user data of: Students in their school classes
   :Reset password of: Students in their school classes whose only role is ``student``
   :Own password reset by: School administrators

.. _roles-permissions-each-role-staff:

Staff
   :Identifier: ``staff``
   :Read user data of: Nobody
   :Reset password of: Nobody
   :Own password reset by: School administrators

.. _roles-permissions-each-role-student:

Student
   :Identifier: ``student``
   :Read user data of: Nobody
   :Reset password of: Nobody
   :Own password reset by: School administrators.
      Teachers of their school classes and legal guardians can reset the password
      only if ``student`` is the user's only role.

.. _roles-permissions-each-role-legal-guardian:

Legal guardian
   :Identifier: ``legal_guardian``
   :Read user data of: Their wards
   :Reset password of: Their wards whose only role is ``student``
   :Own password reset by: School administrators

The following rules apply to every role:

* A user can read their own data, unless ``student`` is their only role.

* A user can filter the list view by the schools they're enrolled in
  and by the school classes and work groups they're a member of.
  A school administrator can also filter by every school class and work group in their school.

* Filtering the list view by role doesn't require a separate permission.
  When you select a role, the filter shows users who hold that role at the selected school
  and whose roles you have permission to read.
  Users can have additional roles.

* Nobody can reset their own password.

* A password reset requires permission for *every* role of the user whose password is reset.
  For example, a teacher can't reset the password of a student who is also a staff member,
  and nobody can reset the password of a user who holds ``school_admin`` in any school.

* A role counts only at the schools where a user holds it,
  and the other user must also have an enrollment at one of those schools.
  The permissions of a legal guardian over their ward depend on their relationship,
  not on whether the guardian holds a role at the same school.
  For details, see :ref:`legal-guardian`.

* The role ``student`` takes nothing away from a user who also holds another role.

.. _legal-guardian:

Legal guardians
===============

Legal guardianship is a relationship between two users
that |UAS| records for both users.
A legal guardian can read the data of their wards because of that relationship alone,
whatever roles or schools either user has.
Resetting the password of a ward also requires that ``student`` is the ward's only role.
To see a ward in the list view,
the legal guardian must have an enrollment at the ward's school.

|UAS| also gives a legal guardian the role ``legal_guardian``
in the school of their wards.
Because of that role, only school administrators can reset the password of a legal guardian,
and a legal guardian can read their own data.
