.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
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

  The backend logs this situation as a warning,
  ``Actor is not a UCS@school user, so this module is unusable for them.``,
  with the account in the data section as ``actor_id``.


Logging
=======

When an error occurs, more details and context can be found in the application logs.
Like with any other UCS application, you can look them up with:

.. code::

   univention-app logs ucsschool-accounts

These logs might not be always helpful to the administrator,
but adding an excerpt of these logs to a bug report is very helpful for error resolution.

Raise :envvar:`ucsschool-accounts/logging/level` to ``DEBUG`` before reproducing a problem.
That adds the technical context of each request, such as the school and group a list view was
filtered by, and which backend answered.

.. _troubleshooting-log-format:

Log format
----------

Each log record follows the Univention log format and looks like this:

.. code::

   2026-09-10T08:22:57.275+00:00 WARNING  [31f863092a] Actor is not a UCS@school user, so this module is unusable for them. Assign a UCS@school role, or use a school account.	| actor_id="administrator" module="ucsschool_accounts_bff.business_logic" line=50 pid=8 request_id="31f863092ade1cb"

A record has five parts:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Part
     - Description
   * - Timestamp
     - The time the record was written, in ISO 8601 and always in UTC,
       so that records of different hosts of a domain can be read as one sequence.
   * - Severity
     - The log level, padded to a fixed width.
   * - Request ID
     - In square brackets, shortened to ten characters.
       It identifies the browser request that produced the record,
       and is a dash for records written outside a request, such as during startup.
   * - Message
     - The event that happened, without any data.
   * - Data
     - Everything after the separator, which is a tab, a pipe and a space (``\t| ``).
       Written as ``key=value`` pairs: first the data belonging to the event,
       then the source code location, the process ID and the request ID in full.
       (Note: All characters of the request ID outside of ``[A-Za-z0-9._:+-]`` are replaced by ``_``.)

To follow a single browser request through the log, take its request ID and search for it.
The application also returns that value in the ``X-Request-ID`` response header,
and reuses the value of an incoming ``X-Request-ID`` request header when one is present.
In the text format, an ID with replaced characters doesn't match the header value;
the structured format keeps it as sent.

Set :envvar:`ucsschool-accounts/logging/structured` to ``True``
to write each record as a single JSON object instead.


User roles can't be modified after creation
==========================================================

Even with the permission to write roles,
you can't modify a user's roles after the user has been created.

This is expected behavior.
Due to restrictions with the Kelvin API,
there are inconsistencies when editing the roles of a user that has multiple roles.
Until this restriction is resolved,
the School Accounts app ignores modifications to user roles.
