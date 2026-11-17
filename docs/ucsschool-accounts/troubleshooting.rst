.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _troubleshooting:

***************
Troubleshooting
***************

This page describes how to troubleshoot common problems with |UASSA|
and how to read the app logs.

.. _troubleshooting-portal-tile:

A user doesn't see the |UASSA| tile in the portal
=================================================

By default, the portal shows the tile to everyone.
If the ``allowedGroups`` attribute of the portal entry names any groups,
the portal shows the tile only to their members.
To check or change those groups, see :ref:`configuration-portal-tile`.

.. _troubleshooting-password-reset-failure:

A password reset fails for some accounts
========================================

After a password reset, the app lists every account
for which it couldn't reset the password or confirm the reset,
with one of the following reasons:

Permission denied
   The signed-in user can't reset the password of that account.
   For the permissions of each role, see :ref:`roles-permissions-and-conditions`.

User not found
   The user account doesn't exist anymore.

Rejected
   Nubus for UCS refused the new password,
   for example, because it doesn't meet the password policy.
   The message states the reason.

Could not be confirmed
   An unexpected error occurred during the reset,
   so the password of that account may or may not have changed.
   The log contains the error as
   ``A password reset could not be confirmed``.

   Check the account before you reset its password again.
   To find out whether the password changed,
   compare the time of the last password change with the time of the reset.
   Run the command in :numref:`troubleshooting-password-reset-check-listing`
   as ``root`` on the
   :external+uv-ucs-operation:term:`Primary Directory Node`
   or a :external+uv-ucs-operation:term:`Backup Directory Node`,
   and replace ``USERNAME`` with the username of the account.

   .. code-block:: console
      :caption: Show the time of the last password change of an account
      :name: troubleshooting-password-reset-check-listing

      $ date -u -d @"$(univention-ldapsearch -LLL "uid=USERNAME" sambaPwdLastSet \
          | sed -n 's/^sambaPwdLastSet: //p')"

   If the command shows a time after the start of the reset,
   the password has changed.
   Compare both times in UTC.
   If you selected :guilabel:`User has to change the password at the next login`,
   a successful reset sets the time to 00:00 UTC on 1 January 1970 instead,
   unless the account already had to change its password before the reset.

This account cannot be required to change its password at the next login
   The option :guilabel:`User has to change the password at the next login` was selected,
   but the *Kelvin REST API* doesn't expose the UDM property ``pwdChangeNextLogin``
   for that account.
   The app left the password unchanged.
   To solve the problem, add ``pwdChangeNextLogin`` to the user properties
   in the *Kelvin REST API* file :file:`/etc/ucsschool/kelvin/mapped_udm_properties.json`.

   For more information,
   see :external+uv-school-kelvin:ref:`configuration-udm-properties`
   in :cite:t:`uv-school-kelvin`.

If no reset succeeds and Nubus for UCS rejects the password for the same reason every time,
the app shows no list.
The dialog stays open and shows the reason after :guilabel:`New password`,
so that you can enter a different password.

.. _troubleshooting-security-token:

"Invalid or missing security token"
===================================

The page that the user worked on is older than their current session,
for example, after they signed in again in another browser tab.
To solve the problem, reload the page.

.. _troubleshooting-invalid-user:

"Not a valid |UAS| user"
========================

Only |UAS| users can use the |UASSA| app.
Accounts without a |UAS| role, such as the ``Administrator`` account,
can't use it.
Sign in with an account that has a |UAS| role.

The app logs this situation as a warning,
``Actor is not a UCS@school user, so this module is unusable for them.``,
with the account in the data section as ``actor_id``.

.. _troubleshooting-logging:

Logging
=======

When an error occurs, the app logs the error with its details and context.
To read the logs, run the command in :numref:`troubleshooting-logging-listing`.

.. code-block:: console
   :caption: Read the logs of the |UASSA| app
   :name: troubleshooting-logging-listing

   $ univention-app logs ucsschool-accounts

Add an excerpt of these logs to a bug report,
even if the messages don't tell you much,
because they help the developers resolve the error.

Before reproducing a problem,
note the current value of :envvar:`ucsschool-accounts/logging/level`
and set it to ``DEBUG``.
The app then logs the technical context of each request,
such as the school and group used to filter a list view
and the backend that answered.
After collecting the relevant logs, restore the previous log level.
For information about changing app settings and the resulting restart,
see :ref:`configuration-app-settings`.

.. _troubleshooting-logging-format:

Log format
==========

Each log record follows the Nubus log format.
In text format, a log record looks like the example
in :numref:`troubleshooting-logging-format-listing`.

.. note::

   The log entry is a single line.
   For better readability, the listing shows each element on a separate line.

.. code-block:: text
   :caption: Log record in the text format
   :name: troubleshooting-logging-format-listing

   2026-09-10T08:22:57.275+00:00
      WARNING
      [31f863092a]
      Actor is not a UCS@school user, so this module is unusable for them. Assign a UCS@school role, or use a school account.
      |
      actor_id="administrator"
      module="ucsschool_accounts.business_logic"
      line=50
      pid=8
      request_id="31f863092ade1cb"

For information about the log format,
see :external+uv-nubus-manual:ref:`nubus-logging-structured-format`
in :cite:t:`uv-nubus-manual`.
The following list explains additional details:

Timestamp
   The time the app wrote the record, in ISO 8601 and always in UTC,
   so that you can read the records of different hosts of a domain as one sequence.

Request ID
   In square brackets, shortened to 10 characters.
   It identifies the browser request that produced the record,
   and is a hyphen for records written outside a request, such as during startup.

Data
   Everything after the separator, which consists of a tab, a pipe, and a space.
   The listing shows only the pipe.
   The app writes the data as ``key=value`` pairs:
   first the data belonging to the event,
   then the source code location, the process ID, and the full request ID.
   The app replaces every character of the request ID outside of ``[A-Za-z0-9._:+-]`` with ``_``.

To follow a single browser request through the log, search for its request ID.
The app returns that value in the ``X-Request-ID`` response header,
and reuses the value of an incoming ``X-Request-ID`` request header when one is present.
In the text format, an ID with replaced characters doesn't match the header value.
The structured format keeps the ID as sent.

To write each record as a single JSON object instead,
set :envvar:`ucsschool-accounts/logging/structured` to ``True``.
