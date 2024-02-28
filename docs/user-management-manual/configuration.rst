.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _configuration:

*************
Configuration
*************

This section is a reference for all app settings of the UCS\@school User Management.
Administrators can configure the settings using
either the :command:`univention-app` command
or the app settings dialog in the
:external+uv-ucs-manual:ref:`App Center UMC module <software-appcenter>`.

The App Center automatically restarts the application after changing any setting.

Kelvin
======

.. envvar:: ucsschool-user-management/kelvin/url

   Defines the URL of the Kelvin REST API for data queries.

Authentication
==============

.. envvar:: ucsschool-user-management/oauth/keycloak-uri

   Defines the base URI of the Keycloak server for authentication.
   If unset, the application tries to derive the URL from the UCR variable
   :external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`
   or falls back to the domain name of the UCS system where you installed the application.

Guardian
========

.. envvar:: ucsschool-user-management/guardian/url

   Defines the URL of the Guardian Authorization API. It usually has the form of ``https://fqdn/guardian/authorization/``
   If unset, the application tries to derive the URL from the domain name of the UCS system where you installed the application.

.. envvar:: ucsschool-user-management/guardian/client_secret

   Defines the client secret of the OAuth2 client to authenticate against the Authorization API with.
   The value is set by the join script to the secret of ``ucsschool-user-management-bff`` when it is first
   installed. Otherwise it has to be set manually.
