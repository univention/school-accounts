.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _changelog:

*********
Changelog
*********

This section lists the changes to the School Accounts app.

.. _release-1-1-0:

v1.1.0 (2026-11-23)
===================

* You can filter the list of users by role, one role at a time.
  The role filter applies to the roles that users hold at the selected school.
  When you select a role before a class or work group,
  the list selects all classes and work groups.
  The browser address contains the selected role,
  so a bookmark or a shared link opens the same list.

* Error messages from Univention Directory Manager (UDM),
  such as the reason a password reset was refused,
  now appear in the language of the user interface.
  Other error messages from the Kelvin REST API remain in English.

* You can search the user list by first name, last name, or username.
  The search ignores upper and lower case and accents.
  A search removes the users it hides from the password reset selection.

* The page shows an error message when a request doesn't reach the app,
  for example when a search query is too long or the connection to the server drops.

* You can export selected users as a CSV file with their first name, last name, and username,
  for example to create a class list.
  Without a selection, the export contains every user that the list shows.
  The export button shows a spinner until the file arrives.

* The app requires UCS 5.2-7 with :uv:erratum:`5.2x701` or later.
  The systems that serve the Univention Portal also need this erratum.
  Without it, Firefox can't save the CSV export.

* You can select users whose passwords you can't reset.
  When you select such a user,
  a red exclamation mark appears next to their checkbox.
  When you try to reset the passwords of selected users,
  a dialog names the users whose passwords you can't reset
  and offers to deselect them.

* When your session expires while you work with the list,
  the app returns you to the same list after you sign in again,
  with the same school, class or work group, and search query.

* For an address that the app doesn't recognize or doesn't open directly,
  the app now shows an error page instead of raw technical output.

* When you can only work with one school,
  the app selects that school for you
  and shows its classes and work groups right away.

.. _release-1-0-0:

v1.0.0 (2026-10-01)
===================

* School Accounts 1.0.0 is the first release of the app.
  School administrators and teachers open it from the Univention Portal
  and work with the user accounts of their school in a web browser.

* You can list the users of a school
  and filter the list by school class or work group.

* You can reset the password of one or more users at once.
  Before the reset, a dialog shows the number of affected accounts.
  For smaller selections, it also lists the individual accounts.
  Teachers can reset the passwords of students in their classes
  whose only role is student.
  School administrators can reset the passwords of users in their school,
  except school administrators.
  For details about permissions, see :ref:`roles-permissions-each-role`.

* The user interface is available in English and German.

* The app requires the Kelvin REST API 4.1.0 or later and the Guardian
  on the same system, and Keycloak in the domain.
