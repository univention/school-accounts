.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _usage:

*****
Usage
*****

This section describes how school administrators, teachers, and legal guardians
use the |UASSA| app to find users, export them, and reset their passwords.
What each of them can see and do depends on their roles,
as described in :ref:`roles-permissions-and-conditions`.

.. _usage-list-users:

List the users of a class or work group
=======================================

To list the users of a school class or a work group,
follow these steps:

#. Open the |UASSA| tile in the
   *Univention Portal*.
   If the portal asks for your credentials, sign in.

#. In the :guilabel:`School` list, select the school.
   The list contains only the schools that you can filter by.

#. In the :guilabel:`Classes & Work Groups` list, select the class or work group.
   To find it in a long list, enter part of its name.
   To list every user of the school, select :guilabel:`All classes and work groups`.

#. Optional: to list only the users with one role,
   select the role in the :guilabel:`Roles` row preceding the table,
   for example :guilabel:`Student`.
   Selecting another role replaces the selected role.
   To list users with any role again,
   select the role once more or select :guilabel:`All`.
   The role filter considers only the roles that a user holds at the selected school.

The list view shows the users matching your selection
with the columns *Last name*, *First name*, *Username*, *Roles*, and *Activated*.
It shows only the users whose data you have permission to read.

To narrow the list, enter one or more words in the search field.
The list then shows only the users for whom every word appears
in the first name, last name, or username.

The words can match different names:
for example, ``anna müller`` finds the user with the first name ``Anna``
and the last name ``Müller``.
The search ignores capitalization and accents:
for example, ``muller`` finds ``Müller``.
It only searches the names that the list shows you,
and it stays active when you select another school, class, work group, or role.

The browser address contains the selected school, group, role, and search.
You can bookmark or share it,
and it opens the same list for every user who has the same permissions.

.. _usage-export-users:

Export users as CSV
===================

You can export selected users as a CSV file,
for example to create a class list for attendance.
To export users, follow these steps:

#. List the users as described in :ref:`usage-list-users`.

#. Select the users that you want to export.
   To select every user on the page, select the checkbox in the table header.
   The export contains deactivated users when you select them.
   Without a selection, the export contains every user that the list shows,
   as narrowed by the filters and the search.

#. Click :guilabel:`Export as CSV`.
   Without a selection, the button reads :guilabel:`Export all as CSV`.
   Your web browser saves the file.
   Its name contains the school and the class or work group that the list shows,
   and the date and time of the export,
   for example ``goethe-gymnasium-berlin_5a_2026-10-27_14_30_00.csv``.

The file has a header row with the columns ``Firstname``, ``Lastname``, and ``Username``,
and one row for each exported user, in the order of the list.
It contains only the data that the list view shows you.
When you may not read the first name or the last name of a user,
the file leaves that field empty.

.. _usage-reset-passwords:

Reset passwords
===============

You can reset a password for one or more users at once.
To reset passwords, follow these steps:

#. List the users as described in :ref:`usage-list-users`.

#. Select the users whose passwords you want to reset.

   To select every user on the page, select the checkbox in the table header.
   A search removes users from the selection when it hides them from the list,
   and clearing the search doesn't select them again,
   so the reset affects only users who appear in the list.

   Search first, then select the users.
   When you select a user whose password you can't reset,
   a red exclamation mark appears next to the checkbox of that user.
   A red exclamation mark on :guilabel:`Reset password` shows
   that the selection contains users whose password you can't reset,
   and the tooltip of the button names them.

#. Click :guilabel:`Reset password`.

   If the selection contains users whose password you can't reset,
   a dialog lists them first.
   Click :guilabel:`Deselect these users` to clear their checkboxes and continue with the others.

   A dialog shows the number of accounts that the reset affects.
   For smaller selections, it also lists the individual accounts.
   The dialog warns you when the selection contains users with different roles
   or when the reset affects many accounts at once.

#. In the :guilabel:`New password` box, enter the password.

   The app sets the same password for every selected account.
   Communicate the password securely to the affected users.

#. Optional: to make the users choose their own password when they sign in next,
   select :guilabel:`User has to change the password at the next login`.
   The dialog offers this option only when the *Kelvin REST API*
   exposes the ``pwdChangeNextLogin`` property of Univention Directory Manager (UDM) users.

#. Select the checkbox that states how many passwords the reset affects,
   and click :guilabel:`Set password`.

The app then shows how many passwords it has reset
and lists the accounts whose resets failed or which the app couldn't confirm, with the reason.
If the app couldn't confirm a reset,
the password may have changed.
Check the account before you reset its password again.
For how to check the account and for other failures,
see :ref:`troubleshooting-password-reset-failure`.

A single reset covers at most 200 users.
If you need to reset more passwords than the limit allows,
select and reset the users in batches.

.. _usage-sign-out:

Sign out
========

To end your session, click :guilabel:`logout` in the page header.
The app also ends your session in Keycloak,
so you need to sign in again when you next visit the app.
