.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _roles-permissions-and-conditions:

*********************************
Roles, permissions and conditions
*********************************

This section is for administrators and covers the default roles and new conditions
introduced with the |UASUMM|.
Roles are managed by another application, the :external+uv-guardian-manual:ref:`Guardian <what-is-the-guardian>`.
For an explanation of the concepts such as
:external+uv-guardian-manual:ref:`roles <terminology-guardian-role>`,
:external+uv-guardian-manual:ref:`capabilities <terminology-guardian-capability>` and
:external+uv-guardian-manual:ref:`permissions <terminology-guardian-permission>`,
please refer to the
:external+uv-guardian-manual:doc:`Guardian manual <index>`.

.. _default-roles:

Default Roles
=============

The default roles added by the |UASUMM| are ``school_admin``, ``teacher``, ``staff`` and ``student``.
Each default role has 1 or more capabilities.

School administrator
--------------------

By default, a user with the school administrator role ``school_admin`` has the following capabilities:


.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Capability Name
    - Description
  * - ``administrate-users-in-same-school``
    - Edit and delete users with the role ``teacher``, ``student`` or ``staff`` in the same school.
  * - ``create-users-general``
    - Click on the add user button in the |UASUMM| interface, provided their school is selected.
  * - ``create-users-in-same-school``
    - Can create users within the same school.
  * - ``school_admin-read-self``
    - Read their own fields.

Teacher
-------

By default, a user with the role ``teacher`` has the following capabilities:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Capability Name
    - Description
  * - ``teacher-read-self``
    - Read their own fields.
  * - ``teacher-read-student``
    - Read fields of students.
  * - ``teacher-write_attribute-students-in-same-class``
    - Teachers can write students passwords and work groups that are in the same class.

Staff
-----

By default, a user with the role ``staff`` has the following capabilities:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70


  * - Capability Name
    - Description
  * - ``staff-read-self``
    - Read their own fields.


Student
-------

By default, a user with the role ``student`` has the following capabilities:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Capability Name
    - Description
  * - ``student-read-self``
    - Read their own fields.

.. _permissions:

Permissions
===========

The |UASUMM| provides :external+uv-guardian-manual:ref:`permissions <terminology-guardian-permission>`
which can be used within the :external+uv-guardian-manual:ref:`Guardian Application <what-is-the-guardian>`
to define what a user with a certain role is permitted to do in the |UASUMM|.

.. note::
    In the current state of the implementation, users with the permission to edit attributes,
    e.g. school class memberships,
    must also be able to read the school attribute of the object to open the edit page.


.. list-table::
  :header-rows: 1
  :align: left
  :widths: 30 70

  * - Permission Name
    - Description
  * - ``Create User Action``
    - Use the :guilabel:`ADD` button in the |UASUMM| to create a user.
  * - ``Delete User Action``
    - Use the :guilabel:`DELETE` button in the |UASUMM| to delete a user.
  * - ``Read Activated``
    - Read the ``Activated`` attribute.
  * - ``Read First Name``
    - Read the ``First Name`` attribute.
  * - ``Read Last Name``
    - Read the ``Last Name`` attribute.
  * - ``Read Roles``
    - Read the ``Roles`` attribute.
  * - ``Read School Classes``
    - Read the ``School Classes`` attribute.
  * - ``Read Work Groups``
    - Read the ``Work Groups`` attribute.
  * - ``Read Schools``
    - Read the ``Schools`` attribute.
  * - ``Write Activated``
    - Write the ``Activated`` attribute.
  * - ``Write First Name``
    - Write the ``First Name`` attribute.
  * - ``Write Last Name``
    - Write the ``Last Name`` attribute.
  * - ``Write Password``
    - Write the ``Password`` attribute.
  * - ``Write Roles``
    - Write the ``Roles`` attribute.
  * - ``Write School Classes``
    - Write the ``School Classes`` attribute.
  * - ``Write Work Groups``
    - Write the ``Work Groups`` attribute.
  * - ``Write Schools``
    - Write the ``Schools`` attribute.
  * - ``Write Username``
    - Write the ``Username`` attribute.

Many permissions follow the form ``Read <attribute>`` or ``Write <attribute>``.
These permissions refer to an attribute of a target user object and
correspond, with some exceptions, to a
:external+uv-school-kelvin:doc:`Kelvin <index>` attribute:

.. list-table::
  :header-rows: 1
  :align: left
  :widths: 40 60

  * - |UASUMM| attribute
    - Kelvin attribute
  * - ``Activated``
    - negated ``disabled``
  * - ``First Name``
    - ``firstname``
  * - ``Last Name``
    - ``lastname``
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
  * - ``Username``
    - ``name``

.. _conditions:

Conditions
==========

|UASUMM| defines four new conditions:

.. _condition-action-is-creation:

.. envvar:: action_is_creation

   This condition is satisfied when a user creates another user with the |UASUMM|.

.. _condition-target-will-have-allowed-roles-only:

.. envvar:: target_will_have_allowed_roles_only

   .. list-table::
      :header-rows: 1
      :align: left
      :width: 50%

      * - Parameter name
        - Value type
      * - roles
        - Comma separated list of ROLE (string)

   This condition is satisfied when all roles of the target of an action, after modification,
   are contained within the roles parameter of the condition.

.. _condition-target-will-be-in-the-same-school-only:

.. envvar:: target_will_be_in_same_school_only

   This condition is satisfied when the actor and the target user are in the same school.

.. _condition-target-shares-school-class-in-school-context:

.. envvar:: target_shares_school_class_in_school_context

   This condition is satisfied when the actor and the target user share a school class
   in the school defined by the context of the actors role currently being evaluated.

.. _condition-actor_is_in_group:

.. envvar:: actor_is_in_group

    This condition is satisfied if the actor is a member of the school classes or work groups
    specified as the target object.

.. _creating-a-new-role:

Creating or modifying a role
============================

While you can create new roles with the Guardian application,
there is currently no way to add roles other than the default roles described above to a user such
that it will be recognized by the |UASUMM|.
But you can modify the existing default roles with the Guardian
and the change of permissions will be respected by the |UASUMM|.

For a detailed explanation on how to modify roles, refer to the section about
:external+uv-guardian-manual:ref:`editing existing roles<editing-existing-roles>` in the Guardian manual.
