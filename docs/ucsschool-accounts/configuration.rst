.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _configuration:

*************
Configuration
*************

This chapter helps administrators configure the portal tile and app settings,
and manage app sessions.

.. _configuration-portal-tile:

Choose who sees the portal tile
===============================

The installation adds a |UASSA| tile to the
*Univention Portal*
and shows it to everyone,
including visitors who aren't signed in.
When visitors select the tile, the portal asks them to sign in first.
The tile doesn't grant any permission.
The app shows every user only what their roles allow,
as described in :ref:`roles-permissions-and-conditions`.

To show the tile to users of the school ``DEMOSCHOOL``,
add the ``Domain Users DEMOSCHOOL`` group to the portal entry
with the command in :numref:`configuration-portal-tile-listing`.
The tile remains visible to members of any other groups
already listed in the entry's ``allowedGroups`` attribute.

To add further schools, repeat the ``--append`` option for each of them.

.. code-block:: console
   :caption: Show the portal tile to users of one school
   :name: configuration-portal-tile-listing

   $ univention-directory-manager portals/entry modify \
       --dn "cn=ucsschool-accounts,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" \
       --append allowedGroups="cn=Domain Users DEMOSCHOOL,cn=groups,ou=DEMOSCHOOL,$(ucr get ldap/base)"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal`
      in :cite:t:`uv-nubus-manual`
      for information about the *Univention Portal*.

.. _configuration-portal-tile-link:

Point the portal tile to another system
=======================================

The domain has one |UASSA| tile,
no matter on how many systems you install the app.
The first installation in the domain creates the tile
and links it to the system where the app runs.
Later installations on other systems leave the tile unchanged.

To let the tile open the app on another system,
for example ``school-accounts.example.com``,
change the link of the portal entry
with the command in :numref:`configuration-portal-tile-link-listing`.
The example sets the link for the ``en_US`` locale.

If the portal and the app use different origins,
check that the app's :envvar:`ucsschool-accounts/frame-ancestors` setting
allows the portal's origin.

.. code-block:: console
   :caption: Point the portal tile to the app on another system
   :name: configuration-portal-tile-link-listing

   $ univention-directory-manager portals/entry modify \
       --dn "cn=ucsschool-accounts,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" \
       --set link='"en_US" "//school-accounts.example.com/univention/ucsschool/ucsschool-accounts/ui/"'

.. _configuration-user-visibility:

User visibility
===============

The |UASSA| app doesn't support configuring which users appear in the list view.
The list view shows a user when the *Guardian* authorization engine
grants the signed-in user at least one permission for that user.
For the permissions of each role, see :ref:`roles-permissions-and-conditions`.

.. _configuration-sessions:

Sessions
========

After a user signs in,
the |UASSA| app keeps the session in an encrypted browser cookie.
The server stores no session data,
so a session survives both a restart of the app and an app update.

.. _configuration-sessions-lifetime:

Session lifetime
----------------

A session lasts at most 8 hours.
Keycloak's own session limits usually end it earlier.
These limits are the realm's *SSO Session Idle* and *SSO Session Max*,
or *Client Session Idle* and *Client Session Max* if the client overrides them.
Users return to the sign-in page when any of these limits expires.

Signing out also ends the session in Keycloak.
A copy of the session cookie keeps working
until the app next refreshes the access token with Keycloak,
which happens within the lifetime of an access token.

Each host encrypts its cookies with its own secret,
so users who switch to the app on another Nubus for UCS system pass through Keycloak again.
While their Keycloak session is open,
they see only a redirect and don't have to enter their credentials.

.. _configuration-sessions-end:

End all sessions on a host
--------------------------

To end every app session on a host,
write a new secret into the :file:`session.secret` file and restart the app.
Run the commands in :numref:`configuration-sessions-end-listing`
as ``root``.

The restart doesn't sign out users of Keycloak,
so their next request takes them back into the app without a credential prompt.
To force users to authenticate again, end their sessions in Keycloak.
Don't delete the :file:`session.secret` file,
because the app generates it only during installation and refuses to start without it.

.. code-block:: console
   :caption: Replace the session secret
   :name: configuration-sessions-end-listing

   $ openssl rand -hex 32 > \
       /var/lib/univention-appcenter/apps/ucsschool-accounts/conf/session.secret
   $ univention-app restart ucsschool-accounts

.. _configuration-sessions-change:

Change the client secret
------------------------

The app authenticates to Keycloak with the client secret in
:file:`/var/lib/univention-appcenter/apps/ucsschool-accounts/conf/client.secret`.
The secret belongs to the domain, and Keycloak holds the authoritative copy.
Every installation and every app update adopts the secret that Keycloak holds.

After you regenerate the secret, a host can't sign users in
until you have updated the secret on that host.

To change the secret, regenerate it for the client ``ucsschool-accounts-ui``
in the *Keycloak Admin Console*.
Then write the new secret into the :file:`client.secret` file
on every host that runs the app, and restart the app there.
Run the commands in :numref:`configuration-sessions-change-listing`
as ``root`` in Bash.
At the prompt, enter the secret from Keycloak.

.. code-block:: console
   :caption: Replace the client secret on a host
   :name: configuration-sessions-change-listing

   $ IFS= read -r -s -p "Client secret: " CLIENT_SECRET
   $ printf '%s\n' "$CLIENT_SECRET" > \
       /var/lib/univention-appcenter/apps/ucsschool-accounts/conf/client.secret
   $ unset CLIENT_SECRET
   $ univention-app restart ucsschool-accounts

.. seealso::

   :external+uv-keycloak:ref:`ad-hoc-provisioning-admin-console-sign-in`
      in :cite:t:`uv-keycloak`
      for information about how to sign in to *Keycloak Admin Console*.

.. _configuration-app-settings:

App settings
============

This section is a reference for all app settings of the |UASSA| app.
You can configure the settings
with the :command:`univention-app` command
or in the app settings dialog.
For more information,
see
:external+uv-ucs-operation:ref:`lifecycle-app-center-after-installation`
in :cite:t:`uv-ucs-operation`.

The Univention App Center restarts the app after you change any setting.

.. envvar:: ucsschool-accounts/kelvin/url

   Defines the hostname of the system that runs the Kelvin REST API.
   If unset, the app uses the fully qualified domain name of the system that it runs on.

.. envvar:: ucsschool-accounts/logging/level

   Sets the log level of the app.
   The values are case-insensitive.

   ``DEBUG`` adds the technical context of each request,
   which helps with a bug report.

   ``TRACE`` additionally logs the start and end of every request.

   An unrecognized log level doesn't keep the app from starting:
   the app logs a warning and uses ``INFO``.

   :Possible values: ``TRACE``, ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``
   :Default value: ``INFO``

.. envvar:: ucsschool-accounts/logging/structured

   If set to ``True``, the app writes each log record as a single JSON object,
   which a log aggregator can parse without a pattern.
   With the value ``False``,
   the app writes the format described in
   :ref:`troubleshooting-logging-format`.

   You can't configure the format itself.
   Both variants follow the Nubus log format,
   so that logs stay consistent across the products of a domain.

   :Default value: ``False``

.. envvar:: ucsschool-accounts/frame-ancestors

   Defines the sites allowed to show the application inside a frame,
   as a space-separated list of sources of the ``Content-Security-Policy`` directive ``frame-ancestors``.
   The portal opens the application inside a frame,
   so the list must contain every system whose portal links to it.

   The value ``'self'`` covers a portal on the Nubus for UCS system
   where you installed the application.

   Add the URL of any other system, for example ``https://primary.example.org``.
   For more information,
   see :ref:`configuration-portal-tile-link`.

   Without a matching entry, the browser refuses to show the application inside the portal.

   :Default value: ``'self'``
   :Possible values: Space-separated list of sources,
      for example ``'self' https://primary.example.org``

.. envvar:: ucsschool-accounts/oauth/keycloak-uri

   Defines the base URI of the Keycloak server that signs users in.
   If unset, the app builds the URI from the hostname in the
   Univention Configuration Registry (UCR) variable
   :external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
   and if that is unset too, from :samp:`ucs-sso-ng.{DOMAIN_NAME}`.
   The app replaces ``DOMAIN_NAME`` with the value of the system's
   UCR variable :external+uv-ucs-operation:envvar:`domainname`.
