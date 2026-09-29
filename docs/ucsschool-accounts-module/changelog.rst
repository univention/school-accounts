.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _changelog:

*********
Changelog
*********

This section lists the changes to the School Accounts app.

.. _release-0-2-0:

0.2.0 (XXXX-XX-XX)
==================

* The app has been renamed from UCS\@school User Management (``ucsschool-user-management``) to
  School Accounts (``ucsschool-accounts``). The App Center treats it as a new app: remove
  ``ucsschool-user-management`` and install ``ucsschool-accounts``. The web interface moves to
  ``/univention/ucsschool/ucsschool-accounts/``, the settings to ``ucsschool-accounts/*`` and the
  Keycloak client to ``ucsschool-accounts-ui``.
* The app requires the Kelvin REST API in version 4.1.0 or later on the same system.
  The installation and the update abort otherwise.
* Sessions are now kept in an encrypted browser cookie instead of in the memory of a single
  process, so they survive a restart of the app and an app update.
* A session now ends at the latest eight hours after the login, even if it is used continuously.
* Logging out now requires a ``POST`` to ``/auth/logout``; a ``GET`` is rejected.
* The Keycloak client the app logs users in with is now confidential. It authenticates
  itself with a client secret that never reaches the browser. The first installation in
  the domain generates the secret; later installations and app updates adopt the one
  already registered at Keycloak.
* The page header shows the logged in user and a button that ends the session.
* The portal tile is visible to everyone instead of only to the members of ``Domain Users``,
  which left out the users of the schools.
* The internal setting ``USER_MANAGEMENT__ADAPTER__SESSION_STORE`` has been removed and is
  ignored if still set.
* The list view no longer shows the school classes and work groups of each user.
* Reset the password of one or more selected users from the list view, with a confirmation
  dialog stating who is affected and per-user results.
* Add school classes and work groups as filter options to the list view.
* The capability ``teacher-set-password-students-in-same-class`` has been renamed to ``teacher-write_attribute-students-in-same-class``.
* The user interface is now fully translated into German. Page title, header, theme toggle, filter
  labels, empty-state messages and the role names in the list view were previously shown in English
  regardless of the browser language.
* The application logs in the Univention log format.
  Set :envvar:`ucsschool-accounts/logging/structured` to ``True``
  to write each record as a single JSON object instead.
  The setting ``ucsschool-user-management/logging/format`` has been removed.

.. _release-0-1-1:

0.1.1 (2024-04-29)
==================

* Fix a bug, where users without school classes could cause errors in the backend.

.. _release-0-1-0:

0.1.0 (2024-04-17)
==================

* Technical preview (not officially supported).
