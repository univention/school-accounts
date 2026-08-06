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
