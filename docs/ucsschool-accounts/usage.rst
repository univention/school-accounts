.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _usage:

*****
Usage
*****

This section describes how school administrators, teachers, and legal guardians
use the |UASSA| app to find users and reset their passwords.
What each of them can see and do depends on their roles,
as described in :ref:`roles-permissions-and-conditions`.

.. _usage-list-users:

List the users of a class or work group
=======================================

To list the users of a school class or a work group,
follow these steps:

#. Open the |UASSA| tile in the
   :external+uv-ucs-manual:ref:`Univention Portal <central-portal>`.
   If Keycloak asks for your credentials, sign in.

#. In the :guilabel:`School` list, select the school.
   The list contains only the schools that you can filter by.

#. In the :guilabel:`Classes & Work Groups` list, select the class or work group.
   To find it in a long list, enter part of its name.
   To list every user of the school, select :guilabel:`All classes and work groups`.

#. Optional: To list only the users with one role,
   select the role in the :guilabel:`Roles` row above the table,
   for example :guilabel:`Student`.
   Selecting another role replaces it.
   To list every role again, select the role once more or select :guilabel:`All`.
   A user counts only with the roles they hold at the selected school.

The list view shows the users of your selection
with the columns *Last name*, *First name*, *Username*, *Roles*, and *Activated*.
It shows only the users whose data you may read.

The browser address contains the selected school, group, and role.
You can bookmark it or share it,
and it opens the same list for every user who has the same permissions.

.. _usage-reset-passwords:

Reset passwords
===============

You can set one new password for one or more users at once.
To reset passwords, follow these steps:

#. List the users as described in :ref:`usage-list-users`.

#. Select the users whose passwords you want to reset.
   The list view shows a checkbox only for the users whose password you can reset.
   To select every such user on the page, select the checkbox in the table header.

#. Click :guilabel:`Reset password`.
   A dialog lists the accounts that the reset affects.
   It warns you when the selection contains users with different roles,
   or when it affects many accounts at once.

#. In the :guilabel:`New password` box, enter the new password.

#. Optional: To make the users choose their own password when they sign in next,
   select :guilabel:`User has to change the password at the next login`.
   The dialog offers this option only when the Kelvin REST API
   exposes the Univention Directory Manager (UDM) property ``pwdChangeNextLogin`` of users.

#. Select the checkbox that states how many passwords the reset affects,
   and click :guilabel:`Set password`.

The app then shows how many passwords it has reset
and lists every account whose password it couldn't reset, with the reason.
A single reset covers at most 200 users.

.. _usage-sign-out:

Sign out
========

To end your session, click :guilabel:`logout` in the page header.
The app also ends your session in Keycloak,
so the next visit asks for your credentials again.
