.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _changelog:

*********
Changelog
*********

This section lists the changes to the School Accounts app.

.. _release-1-1-0:

v1.1.0 (unreleased)
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
  A search removes the users that it hides from the selection for the password reset.
* The page shows an error message when a request does not reach the app,
  for example when a search text is too long or the connection to the server drops.
* You can export selected users as a CSV file with their first name, last name, and username,
  for example to create a class list.
  Without a selection, the export contains every user that the list shows.
  The export button shows a spinner until the file arrives.
* The app requires UCS 5.2-7 with :uv:erratum:`5.2x701` or later,
  on the systems that serve the Univention Portal as well.
  Without this erratum, Firefox can't save the CSV export.
* You can select users whose password you can't reset.
  A red exclamation mark next to the checkbox marks them.
  When you reset the passwords of such a selection,
  a dialog names these users and offers to deselect them.
* When your session expires while you work with the list,
  the app returns you to the same list after you sign in again,
  with its school, class or work group, and search.
* An address that the app doesn't know, or doesn't open directly,
  now shows an error message page instead of raw technical output.

.. _release-1-0-0:

v1.0.0 (2026-10-01)
===================

* School Accounts 1.0.0 is the first release of the app.
  School administrators and teachers open it from the Univention Portal
  and work with the user accounts of their school in a web browser.
* You can list the users of a school
  and filter the list by school class or work group.
* You can reset the password of one or more users at once.
  A confirmation dialog shows who is affected before anything changes.
  Teachers can reset the passwords of the students in their classes.
  School administrators can reset the passwords of the other users of their school.
* The user interface is available in English and German.
* The app requires the Kelvin REST API 4.1.0 or later and the Guardian
  on the same system, and Keycloak in the domain.
