.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _configuration:

*************
Configuration
*************

Portal tile for the |UASUMM|
==============================

You can adjust the portal tile visibility of the |UASUMM|
by following the UCS manual section about the :external+uv-ucs-manual:ref:`Portal <central-portal>`.

As a quick example for the command line, to add all domain users of the school ``DEMOSCHOOL``, you can run:

.. code:: bash

   udm portals/entry modify --dn "cn=ucsschool-user-management,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)"\
   --append allowedGroups="cn=Domain Users DEMOSCHOOL,cn=groups,ou=DEMOSCHOOL,$(ucr get ldap/base)"

User visibility
===============

User visibility in the list view can only be changed implicitly:
The user of the |UASUMM| can see other users in the list view for which Cerbos
has granted at least one permission.

Sessions
========

After an interactive login, the |UASUMM| keeps the session entirely in an
encrypted browser cookie. No session data is stored on the server, so every
worker process of the app can serve any request, and a session survives both a
restart of the app and an app update.

The cookie is encrypted, not only signed, because it carries the tokens the app
needs to renew the login against Keycloak without prompting the user again.
The key is derived from a secret that the app generates once per host during
installation, in
:file:`/var/lib/univention-appcenter/apps/ucsschool-user-management/conf/session.secret`.
An update reuses an existing file and therefore keeps existing sessions valid.

A session lasts at most eight hours. Renewing the tokens extends the login
within that window but never beyond it, so after eight hours users log in again.

This model has three limitations that administrators should know about:

No revocation before expiry
   The app cannot invalidate an individual session. A copy of the cookie keeps
   working for the rest of the eight hours. Logging out shortens that: the copy
   stops working once the app next renews the login against Keycloak, which
   happens within the lifetime of an access token.

One login per UCS system
   Each host generates its own secret, so a session established on the
   :external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node` is not valid on a
   :external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`, or the other way
   round. Users log in once per system they use.

Replacing the secret is the only way to end all sessions at once
   Writing a new secret into the :file:`session.secret` file and restarting the
   app ends every session on that host at once, for example with
   :command:`openssl rand -hex 32 > session.secret`. Do not delete the file:
   the app only generates it during installation and refuses to start without
   it.

App Settings
============

This section is a reference for all app settings of the |UASUMM|.
Administrators can configure the settings using
either the :command:`univention-app` command
or the app settings dialog in the
:external+uv-ucs-manual:ref:`App Center UMC module <software-appcenter>`.

The App Center automatically restarts the application after changing any setting.

Kelvin
------

.. envvar:: ucsschool-user-management/kelvin/url

   Defines the URL of the Kelvin REST API for data queries. If not set, the URL is generated from hostname and domain name.

Authentication
--------------

.. envvar:: ucsschool-user-management/oauth/keycloak-uri

   Defines the base URI of the Keycloak server for authentication.
   If unset, the application tries to derive the URL from the UCR variable
   :external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`
   or falls back to the domain name of the UCS system where you installed the application.
