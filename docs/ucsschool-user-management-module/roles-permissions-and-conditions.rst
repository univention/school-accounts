.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _roles-permissions-and-conditions:

**********************
Roles and permissions
**********************

This section is for administrators and covers the default roles and permissions
used by the |UASUMM|.
Authorization decisions are made by the
:external+uv-guardian-manual:ref:`Guardian <what-is-the-guardian>`,
using a policy bundle that ships with the |UASUMM|.
For an explanation of general concepts such as
:external+uv-guardian-manual:ref:`roles <terminology-guardian-role>` and
:external+uv-guardian-manual:ref:`permissions <terminology-guardian-permission>`,
please refer to the
:external+uv-guardian-manual:doc:`Guardian manual <index>`.

.. _default-roles:

Default Roles
=============

The default roles used by the |UASUMM| are ``school_admin``, ``teacher``, ``staff`` and ``student``.
Each role has the following permissions on other users in the same school.
Regardless of role, every user can always read their own data, and can filter the list view by
the schools they're enrolled in and the school classes or work groups they're a member of.

School administrator
--------------------

A user with the school administrator role ``school_admin`` can, for every user in their own school:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``Read``
    - Read all readable attributes, see :ref:`permissions`.
  * - ``Write Password``
    - Reset the password, unless the target user is also a ``school_admin``.

A school administrator can also filter by any school class or work group in their own school.

Teacher
-------

A user with the role ``teacher`` can, for students who share a class with them in the same school:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``Read``
    - Read all readable attributes, see :ref:`permissions`.
  * - ``Write Password``
    - Reset the password.

Staff
-----

A user with the role ``staff`` can, for every user in their own school:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission
    - Description
  * - ``Read``
    - Read all readable attributes, see :ref:`permissions`.

Student
-------

A user with the role ``student`` has no permissions on other users.
Like every user, they can read their own data.

.. _permissions:

Permissions
===========

The |UASUMM| provides the following permissions, which the roles above are granted on other users:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission Name
    - Description
  * - ``Read First Name``
    - Read the ``First Name`` attribute.
  * - ``Read Last Name``
    - Read the ``Last Name`` attribute.
  * - ``Read Disabled``
    - Read the ``Disabled`` attribute.
  * - ``Read Activated``
    - Read the ``Activated`` attribute.
  * - ``Read Email``
    - Read the ``Email`` attribute.
  * - ``Read Birthday``
    - Read the ``Birthday`` attribute.
  * - ``Read Expiration Date``
    - Read the ``Expiration Date`` attribute.
  * - ``Read Roles``
    - Read the ``Roles`` attribute.
  * - ``Read School Classes``
    - Read the ``School Classes`` attribute.
  * - ``Read Work Groups``
    - Read the ``Work Groups`` attribute.
  * - ``Read Schools``
    - Read the ``Schools`` attribute.
  * - ``Write Password``
    - Write the ``Password`` attribute.
  * - ``Use As Filter``
    - Filter the list view by a school, school class or work group.

Permissions of the form ``Read <attribute>`` refer to an attribute of a target user object and
correspond, with some exceptions, to a
:external+uv-school-kelvin:doc:`Kelvin <index>` attribute:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 40 60

  * - |UASUMM| attribute
    - Kelvin attribute
  * - ``First Name``
    - ``firstname``
  * - ``Last Name``
    - ``lastname``
  * - ``Disabled``
    - ``disabled``
  * - ``Activated``
    - negated ``disabled``
  * - ``Email``
    - ``email``
  * - ``Birthday``
    - ``birthday``
  * - ``Expiration Date``
    - ``expiration_date``
  * - ``Roles``
    - not applicable
  * - ``School Classes``
    - ``school_classes``
  * - ``Work Groups``
    - ``workgroups``
  * - ``Schools``
    - ``schools``
  * - ``Password``
    - ``password``

.. note::
    The roles and permissions described in this section are fixed by the |UASUMM|'s policy bundle.
    There is currently no administrative interface for creating custom roles or
    changing which permissions a role has.
