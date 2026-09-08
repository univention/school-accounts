.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _changelog:

*********
Changelog
*********

This section lists the changes to the User Management Module.

.. _release-0-2-0:

0.2.0 (XXXX-XX-XX)
==================

* Sessions are now kept in an encrypted browser cookie instead of in the memory of a single
  process, so they survive a restart of the app and an app update.
* A session now ends at the latest eight hours after the login, even if it is used continuously.
* Logging out now requires a ``POST`` to ``/auth/logout``; a ``GET`` is rejected.
* The internal setting ``USER_MANAGEMENT__ADAPTER__SESSION_STORE`` has been removed and is
  ignored if still set.
* Add work groups as a new attribute to the list view.
* Add school classes and work groups as filter options to the list view.
* The capability ``teacher-set-password-students-in-same-class`` has been renamed to ``teacher-write_attribute-students-in-same-class``.
* The user interface is now fully translated into German. Page title, header, theme toggle, filter
  labels, empty-state messages and the role names in the list view were previously shown in English
  regardless of the browser language.

.. _release-0-1-1:

0.1.1 (2024-04-29)
==================

* Fix a bug, where users without school classes could cause errors in the backend.

.. _release-0-1-0:

0.1.0 (2024-04-17)
==================

* Technical preview (not officially supported).
