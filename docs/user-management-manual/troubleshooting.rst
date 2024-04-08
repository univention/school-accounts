.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _troubleshooting:

***************
Troubleshooting
***************

The |UASUMM| tile on the portal page is not visible for a user
==============================================================

The module is only visible for users which are members of a group which is in turn
added to the attribute ``allowedGroups`` of the portal entry object. Refer to the
:external+uv-ucs-manual:ref:`Portal <central-portal>` section of the UCS Manual.

Backend returns Status code 403: Forbidden
==========================================

This usually means that the user that is currently logged in, does not have sufficient permissions for the
selected action.

Please refer to your system administrator to clarify which roles are allowed to use which functionality.

.. note::

  This module is only usable by UCS\@school users.
  This is different from the previous versions of the UCS\@school Users module,
  which can be used by the ``Administrator`` account as well.

  This situation is documented in the backend logs with the message ``The logged in user 'administrator' is not a valid UCS@school user.``


Logging
=======

When an error occurs, more details and context can be found in the application logs.
Like with any other UCS application, you can look them up with:

.. code::

   univention-app logs ucsschool-user-management

These logs might not be always helpful to the administrator,
but adding an excerpt of these logs to a bug report is very helpful for error resolution.


User roles can't be modified after creation
==========================================================

Even with the permission to write roles,
you can't modify a user's roles after the user has been created.

This is expected behavior.
Due to restrictions with the Kelvin API,
there are inconsistencies when editing the roles of a user that has multiple roles.
Until this restriction is resolved,
the User Management Module ignores modifications to user roles.
