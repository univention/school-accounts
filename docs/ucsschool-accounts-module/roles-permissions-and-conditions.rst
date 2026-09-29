.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _roles-permissions-and-conditions:

**********************
Roles and permissions
**********************

This section is for administrators and covers the default roles and permissions
used by the |UASUMM|.
The :external+uv-nubus-manual:ref:`Guardian <nubus-authorization>` makes the
authorization decisions, using a policy bundle that ships with the |UASUMM|.
For more information about how the Guardian reaches a decision
and where its policies come from,
see :external+uv-nubus-manual:doc:`Authorization <authorization>`.

.. _default-roles:

Default roles
=============

The default roles used by the |UASUMM| are ``school_admin``, ``teacher``,
``staff``, and ``student``.
The following sections list the permissions each role has on other users in the
same school.
Some rules apply whatever role a user holds:

* Every user can read their own data, unless ``student`` is their only role.
* Every user can filter the list view by the schools they're enrolled in and the
  school classes or work groups they're a member of.
* No user can reset their own password.
* A password reset requires the user doing it to be allowed to reset *every*
  role the target holds, not only one of them.
  A teacher can reset a student's password, but not the password of a student
  who is also a staff member, a legal guardian, or a teacher, because a teacher
  can reset none of those.
* A role only allows a reset at the schools the user holds it in, and the target
  must be enrolled in one of them.
  A teacher who administers a second school gains nothing over the users of the
  school they teach in.
  Once the target is enrolled in such a school, the role covers every role the
  target holds, wherever they hold it.
  A school administrator who is given a role at a second school therefore keeps
  every reset they had.
* A role that grants no permissions of its own, such as ``staff``, still
  protects its holder's password this way.
* No user can reset the password of a user who holds the ``school_admin`` role,
  whatever school that user holds it in, and the same applies to any further
  role the directory service assigns.

Legal guardianship gives a user permissions on another user as well.
The directory service records it as a relationship between two users, in an
attribute on each of them.
The permissions follow from that relationship and not from the
``legal_guardian`` role that comes with it.
For more information about legal guardianship, see :ref:`legal-guardian`.

School administrator
--------------------

A user with the school administrator role ``school_admin`` has the following
permissions on every user in their own school:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``read-*``
    - Read all readable attributes.
      For more information, see :ref:`permissions`.
  * - ``write-password``
    - Reset the password, unless the target user holds the ``school_admin`` role
      in any school.

A school administrator can also filter by any school class or work group in
their own school.

Teacher
-------

A user with the role ``teacher`` has the following permissions on students who
share a class with them in the same school:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``read-*``
    - Read all readable attributes.
      For more information, see :ref:`permissions`.
  * - ``write-password``
    - Reset the password of a student, unless the student holds any other role.

Staff
-----

A user with the role ``staff`` has no permissions on other users.
Like every user who holds a role other than ``student``, they can read their own
data.
The role grants nothing, but it does protect its holder: only a school
administrator can reset the password of a user who holds ``staff``, even one who
is also a student in a teacher's own class.

Student
-------

A user whose only role is ``student`` has no permissions on user data.
Such a user can't read the data of other users, and can't read their own data either.
The ``use-as-filter`` permission on their own schools, school classes, and work
groups is all they keep, so they can still filter the list view, but the list of
users stays empty.

The role ``student`` takes nothing away from a user who also holds another role.
A teacher at one school who is enrolled as a student at another school
keeps the teacher permissions, and can read their own data.

.. _legal-guardian:

Legal guardian
==============

Legal guardianship is a relationship between two users, recorded in the directory
service: the guardian has an attribute naming their wards, and each ward has an
attribute naming their guardians.
The permissions in the following table follow from that relationship alone.
They don't depend on the roles or schools of either user, and there is no ward
role at all.

A user who is a legal guardian of another user, their ward, has the following
permissions on that ward:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``read-*``
    - Read all readable attributes.
      For more information, see :ref:`permissions`.
  * - ``write-password``
    - Reset the password, but only while ``student`` is the ward's only role.

The directory service does give a guardian the ``legal_guardian`` role in the
school their wards attend.
The role has two effects on this module.
On password resets, a school administrator can reset a parent's password in their
own school, and nobody else can.
On the read of a user's own data, ``legal_guardian`` counts as a role other than
``student``, so a guardian who is otherwise only a student can read their own
data.

The password reset is the one exception to guardianship being independent of
roles, and it's stricter than the rule for the roles in :ref:`default-roles`.
A legal guardian can reset a ward's password only while that ward holds the
``student`` role and no other role.
A ward enrolled as a student at more than one school still holds only the
``student`` role.
Any second role takes the reset away, whether it's ``teacher``, ``staff``,
``school_admin``, ``legal_guardian``, or any further role the directory service
assigns.
So does holding no role at all: a user without a school role isn't a student.
The reads in the preceding table are unaffected, whatever roles the ward holds.

To see a ward in the list view, a legal guardian must be able to filter by the
ward's school.
This means the legal guardian must be enrolled in that school themselves.

.. _permissions:

Permissions
===========

The |UASUMM| provides the following permissions, which the roles described
earlier hold on other users:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``read-first_name``
    - Read the ``first_name`` attribute.
  * - ``read-last_name``
    - Read the ``last_name`` attribute.
  * - ``read-disabled``
    - Read the ``disabled`` attribute.
  * - ``read-activated``
    - Read the ``activated`` attribute.
  * - ``read-email``
    - Read the ``email`` attribute.
  * - ``read-birthday``
    - Read the ``birthday`` attribute.
  * - ``read-expiration_date``
    - Read the ``expiration_date`` attribute.
  * - ``read-roles``
    - Read the ``roles`` attribute.
  * - ``read-school_classes``
    - Read the ``school_classes`` attribute.
  * - ``read-work_groups``
    - Read the ``work_groups`` attribute.
  * - ``read-schools``
    - Read the ``schools`` attribute.
  * - ``write-password``
    - Write the ``password`` attribute.
  * - ``use-as-filter``
    - Filter the list view by a school, school class, or work group.

Each ``read-ATTRIBUTE`` and ``write-ATTRIBUTE`` permission refers to an attribute
of a target user object, and most attributes correspond to a
:external+uv-school-kelvin:doc:`Kelvin <index>` attribute:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 40 60

  * - |UASUMM| attribute
    - Kelvin attribute
  * - ``first_name``
    - ``firstname``
  * - ``last_name``
    - ``lastname``
  * - ``disabled``
    - ``disabled``
  * - ``activated``
    - negated ``disabled``
  * - ``email``
    - ``email``
  * - ``birthday``
    - ``birthday``
  * - ``expiration_date``
    - ``expiration_date``
  * - ``roles``
    - not applicable
  * - ``school_classes``
    - ``school_classes``
  * - ``work_groups``
    - ``workgroups``
  * - ``schools``
    - ``schools``
  * - ``password``
    - ``password``

.. note::

   The policy bundle of the |UASUMM| app fixes the roles and permissions described
   in this section.
   The |UASUMM| app provides no administrative interface for creating custom roles
   or changing which permissions a role has.
