.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _troubleshooting:

***************
Troubleshooting
***************

A user doesn't see the |UASUMM| tile in the portal
==================================================

By default, the portal shows the tile to everyone.
If the ``allowedGroups`` attribute of the portal entry names any groups,
the portal shows the tile only to their members.
To check or change those groups, see :ref:`configuration-portal-tile`.

A password reset fails for some accounts
========================================

After a password reset, the app lists every account whose password it couldn't reset,
with one of the following reasons:

Permission denied
   The signed-in user can't reset the password of that account.
   For the permissions of each role, see :ref:`roles-permissions-and-conditions`.

User not found
   The account doesn't exist anymore.

Rejected
   UCS refused the new password,
   for example because it doesn't meet the password policy.
   The message that follows states the reason.

A user sees "Invalid or missing security token"
===============================================

The page that the user worked on is older than their current session,
for example after they signed in again in another browser tab.
To solve the problem, reload the page.

A user sees "not a valid UCS\@school user"
==========================================

Only UCS\@school users can use the |UASUMM| app.
Accounts without a UCS\@school role, such as the ``Administrator`` account,
can't use it.

The app logs this situation as a warning,
``Actor is not a UCS@school user, so this module is unusable for them.``,
with the account in the data section as ``actor_id``.

.. _troubleshooting-logging:

Logging
=======

When an error occurs, the app logs the error with its details and context.
To read the logs, run the following command:

.. code-block:: console
   :caption: Read the logs of the |UASUMM| app

   $ univention-app logs ucsschool-accounts

Add an excerpt of these logs to a bug report,
even when the messages don't tell you much,
because they help the developers resolve the error.

Before reproducing a problem,
set :envvar:`ucsschool-accounts/logging/level` to ``DEBUG``.
The app then logs the technical context of each request,
such as the school and group that a list view was filtered by,
and which backend answered.

.. _troubleshooting-log-format:

Log format
----------

Each log record follows the Univention log format and looks like the following example:

.. code-block:: text
   :caption: Log record in the text format

   2026-09-10T08:22:57.275+00:00 WARNING  [31f863092a] Actor is not a UCS@school user, so this module is unusable for them. Assign a UCS@school role, or use a school account.	| actor_id="administrator" module="ucsschool_accounts_bff.business_logic" line=50 pid=8 request_id="31f863092ade1cb"

A record consists of the following five parts:

.. list-table:: Parts of a log record
   :header-rows: 1
   :align: left
   :widths: 20 80

   * - Part
     - Description
   * - Timestamp
     - The time the app wrote the record, in ISO 8601 and always in UTC,
       so that you can read the records of different hosts of a domain as one sequence.
   * - Severity
     - The log level, padded to a fixed width.
   * - Request ID
     - In square brackets, shortened to 10 characters.
       It identifies the browser request that produced the record,
       and is a hyphen for records written outside a request, such as during startup.
   * - Message
     - The event that happened, without any data.
   * - Data
     - Everything after the separator, which is a tab, a pipe, and a space (``\t| ``).
       Written as ``key=value`` pairs: first the data belonging to the event,
       then the source code location, the process ID, and the full request ID.
       The app replaces every character of the request ID outside of ``[A-Za-z0-9._:+-]`` with ``_``.

To follow a single browser request through the log, search for its request ID.
The app returns that value in the ``X-Request-ID`` response header,
and reuses the value of an incoming ``X-Request-ID`` request header when one is present.
In the text format, an ID with replaced characters doesn't match the header value.
The structured format keeps the ID as sent.

To write each record as a single JSON object instead,
set :envvar:`ucsschool-accounts/logging/structured` to ``True``.
