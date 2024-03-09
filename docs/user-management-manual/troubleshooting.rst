.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _troubleshooting:

***************
Troubleshooting
***************

Backend returns Status code 403: Forbidden
==========================================

This usually means that the user that is currently logged in, does not have sufficient permissions for the
selected action.

Please refer to your system administrator to clarify which roles are allowed to use which functionality.

.. note::

  This module is only usable by UCS\@school users.
  This is different from the normal UCS\@school Users module, which can be used by the ``Administrator`` account as well.

  This situation is documented in the backend logs with the message ``The logged in user 'administrator' is not a valid UCS@school user.``
