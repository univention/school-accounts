.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _configuration:

*************
Configuration
*************

.. _configuration-portal-tile:

Choose who sees the portal tile
===============================

The installation adds a |UASUMM| tile to the
:external+uv-ucs-manual:ref:`Univention Portal <central-portal>`
and shows it to everyone,
including visitors who aren't signed in.
Selecting the tile asks them to sign in first.
The tile doesn't grant any permission.
The app shows every user only what their roles allow,
as described in :ref:`roles-permissions-and-conditions`.

To show the tile only to the users of the school ``DEMOSCHOOL``,
add the ``Domain Users DEMOSCHOOL`` group of that school to the portal entry:

.. code-block:: console
   :caption: Show the portal tile only to the users of one school

   $ univention-directory-manager portals/entry modify \
       --dn "cn=ucsschool-accounts,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" \
       --append allowedGroups="cn=Domain Users DEMOSCHOOL,cn=groups,ou=DEMOSCHOOL,$(ucr get ldap/base)"

To add further schools, repeat the ``--append`` option for each of them.

User visibility
===============

You can't configure which users appear in the list view.
The list view shows a user when the Guardian grants the signed-in user
at least one permission on them.
For the permissions of each role, see :ref:`roles-permissions-and-conditions`.

.. _configuration-sessions:

Sessions
========

After a user signs in,
the |UASUMM| app keeps the session in an encrypted browser cookie.
The server stores no session data,
so a session survives both a restart of the app and an app update.

Session lifetime
----------------

A session lasts at most 8 hours.
Keycloak's own session limits usually end it earlier:
the realm's *SSO Session Idle* and *SSO Session Max*,
or *Client Session Idle* and *Client Session Max* if the client overrides them.
Whichever limit runs out first sends users back to the sign-in page.

Signing out also ends the session in Keycloak.
A copy of the session cookie keeps working
until the app next renews the sign-in against Keycloak,
which happens within the lifetime of an access token.

Each host encrypts its cookies with its own secret,
so users who switch to the app on another UCS system pass through Keycloak again.
While their Keycloak session is open,
they see only a redirect and don't have to enter their credentials.

End all sessions on a host
--------------------------

To end every app session on a host,
write a new secret into the :file:`session.secret` file and restart the app:

.. code-block:: console
   :caption: Replace the session secret

   $ openssl rand -hex 32 > \
       /var/lib/univention-appcenter/apps/ucsschool-accounts/conf/session.secret
   $ univention-app restart ucsschool-accounts

This doesn't sign users out of Keycloak,
so their next request takes them back into the app without a credential prompt.
To force users to authenticate again, end their sessions in Keycloak.
Don't delete the :file:`session.secret` file:
the app generates it only during installation and refuses to start without it.

Change the client secret
------------------------

The app authenticates to Keycloak with the client secret in
:file:`/var/lib/univention-appcenter/apps/ucsschool-accounts/conf/client.secret`.
The secret belongs to the domain, and Keycloak holds the authoritative copy.
To change it, change it in Keycloak and then run
:command:`univention-run-join-scripts` on every host that runs the app.

.. _app-settings:

App settings
============

This section is a reference for all app settings of the |UASUMM| app.
You can configure the settings
with the :command:`univention-app` command
or in the app settings dialog of the
:external+uv-ucs-manual:ref:`App Center UMC module <software-appcenter>`.

The Univention App Center restarts the app after you change any setting.

Kelvin
------

.. envvar:: ucsschool-accounts/kelvin/url

   Defines the hostname of the system that runs the Kelvin REST API.
   If unset, the app uses the fully qualified domain name of the system that it runs on.

Logging
-------

.. envvar:: ucsschool-accounts/logging/level

   Sets the log level of the app.
   Possible values are ``TRACE``, ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, and ``CRITICAL``,
   with ``INFO`` as the default.
   The values are case-insensitive.
   ``DEBUG`` adds the technical context of each request,
   which helps with a bug report.
   ``TRACE`` additionally logs the start and end of every request.
   A value that names no level doesn't keep the app from starting:
   the app logs a warning and uses ``INFO``.

.. envvar:: ucsschool-accounts/logging/structured

   If set to ``True``, the app writes each log record as a single JSON object,
   which a log aggregator can parse without a pattern.
   The default is ``False``, which writes the format described in :ref:`troubleshooting-log-format`.

   You can't configure the format itself.
   Both variants follow the Univention log format,
   so that logs stay consistent across the products of a domain.

Authentication
--------------

.. envvar:: ucsschool-accounts/oauth/keycloak-uri

   Defines the base URI of the Keycloak server that signs users in.
   If unset, the app builds the URI from the hostname in the
   Univention Configuration Registry (UCR) variable
   :external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
   and if that is unset too, from :samp:`ucs-sso-ng.{DOMAIN_NAME}`.
