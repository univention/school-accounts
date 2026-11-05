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
