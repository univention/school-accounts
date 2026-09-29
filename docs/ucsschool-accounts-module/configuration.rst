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

After a user signs in, the |UASUMM| app keeps the session entirely in an
encrypted browser cookie. The server stores no session data, so every
worker process of the app can serve any request, and a session survives both a
restart of the app and an app update.

The app encrypts the cookie rather than only signing it, because it carries the tokens the app
needs to renew the sign-in against Keycloak without prompting the user again.
The app derives the key from a secret that it generates once per host during
installation, in
:file:`/var/lib/univention-appcenter/apps/ucsschool-accounts/conf/session.secret`.
An update reuses an existing file and therefore keeps existing sessions valid.

The app signs users in through a confidential Keycloak client. It proves its own
identity to Keycloak with a client secret in
:file:`/var/lib/univention-appcenter/apps/ucsschool-accounts/conf/client.secret`.
The secret never reaches the browser.

The Keycloak client belongs to the domain rather than to a single host, and so
does its secret. The first installation in the domain registers a generated
secret. Every later installation, and every app update, adopts the secret that
Keycloak already holds and restarts the app. Keycloak therefore keeps the
authoritative copy: to change the secret, change it in Keycloak and then run
:command:`univention-run-join-scripts` on every host that runs the app.

A session lasts at most 8 hours.
Renewing the tokens extends the sign-in within that window but never beyond it.

Eight hours is the ceiling the app enforces, not the lifetime users experience.
Keycloak applies its own session limits on top of it,
and those usually end the session earlier.
The app renews the sign-in only after the access token has expired,
and Keycloak refuses that renewal once it has closed the user's session:
after the realm's *SSO Session Idle* has passed
without the user working in the app,
or at the latest after its *SSO Session Max*.
A client can override both with *Client Session Idle* and *Client Session Max*.
Whichever limit runs out first is the one that sends users back to the sign-in page.

This model has the following three limitations:

No revocation before expiry
   The app can't invalidate an individual session.
   A copy of the cookie keeps working for the rest of the session's lifetime.
   Signing out shortens that:
   it ends the session in Keycloak as well,
   so the copy stops working once the app next renews the sign-in against Keycloak,
   which happens within the lifetime of an access token.

One app session per UCS system
   Each host generates its own secret,
   so the session from the
   :external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node`
   isn't valid on a
   :external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`,
   or the other way round.
   Users pass through Keycloak again on the second system.
   Keycloak keeps its own session for the user, independently of this app,
   so as long as that session is still open,
   they see only a redirect and Keycloak doesn't ask for their credentials again.

Replacing the secret ends the app sessions, but doesn't sign anybody out
   To invalidate every cookie on a host at once,
   write a new secret into the :file:`session.secret` file and restart the app,
   for example with :command:`openssl rand -hex 32 > session.secret`.
   This doesn't lock users out.
   Their Keycloak sessions survive it,
   so the next request takes them through Keycloak
   and back into the app without a credential prompt.
   To force users to authenticate again, end their sessions in Keycloak.
   Don't delete the :file:`session.secret` file:
   the app generates it only during installation and refuses to start without it.

.. _app-settings:

App settings
============

This section is a reference for all app settings of the |UASUMM| app.
You can configure the settings
with the :command:`univention-app` command
or in the app settings dialog of the
:external+uv-ucs-manual:ref:`App Center UMC module <software-appcenter>`.

The App Center restarts the app after you change any setting.

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
   written in any case, with ``INFO`` as the default.
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
   If unset, the app uses the UCR variable
   :external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
   and if that is unset too, ``ucs-sso-ng`` followed by the domain name.
