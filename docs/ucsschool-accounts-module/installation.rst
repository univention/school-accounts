.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _installation:

************
Installation
************

This section is for administrators
and covers the installation, upgrade, and removal of the |UASUMM| app.

.. _installation_instructions:

Install the app
===============

You can install the |UASUMM| app on a
:external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node` or on a
:external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`
that runs Univention Corporate Server (UCS) 5.2-6 with :uv:erratum:`5.2x569` or later.

Your domain must meet the following prerequisites before you install the app:

* :external+uv-school-manual:ref:`UCS@school <introduction>` is installed and configured in the domain.
* The Guardian (``univention-guardian``) is installed and configured
  on the same system as the |UASUMM| app.
  For more information, see :external+uv-ucs-operation:ref:`iam-authorization-engine-install`.
* The :external+uv-school-kelvin:doc:`Kelvin REST API <index>` in version 4.1.0 or later
  is installed and configured
  on the same system as the |UASUMM| app.
  The installation and the update of the |UASUMM| app abort otherwise.
* Keycloak is installed and configured in the domain as the identity provider.
  For more information about installing Keycloak,
  see the :external+uv-keycloak:ref:`Univention Keycloak app documentation <app-installation>`.

To install the |UASUMM| app from the command line,
run the following command:

.. code-block:: console
   :caption: Install the |UASUMM| app from the command line

   $ univention-app install ucsschool-accounts

After the installation,
users reach the app through the
:external+uv-ucs-manual:ref:`Univention Portal <central-portal>`.
To choose who sees the portal tile, see :ref:`configuration-portal-tile`.

.. _migration:

Migrate from UCS\@school User Management
========================================

The |UASUMM| app replaces the UCS\@school User Management app
(``ucsschool-user-management``).
The Univention App Center treats it as a different app,
so an upgrade doesn't turn one into the other.
To migrate, remove the old app and install the new one on every system that runs it:

.. code-block:: console
   :caption: Replace UCS\@school User Management with |UASUMM|

   $ univention-app remove ucsschool-user-management
   $ univention-app install ucsschool-accounts

The app settings don't carry over,
because the setting names changed
from ``ucsschool-user-management/*`` to ``ucsschool-accounts/*``.
Set the settings again after the installation.
For the list of settings, see :ref:`app-settings`.

The old app leaves its Keycloak client ``ucsschool-user-management-ui`` behind.
You can remove it as described in :ref:`remove-keycloak-client`.

.. _upgrade:

Upgrade the app
===============

To upgrade the |UASUMM| app to a later version,
run the following command:

.. code-block:: console
   :caption: Upgrade the |UASUMM| app from the command line

   $ univention-app upgrade ucsschool-accounts

.. _removal:

Remove the app
==============

To remove the |UASUMM| app from a system,
run the following command:

.. code-block:: console
   :caption: Remove the |UASUMM| app from the command line

   $ univention-app remove ucsschool-accounts

The removal deletes the portal tile and the policies of the app.
It keeps the Keycloak client,
because other systems in the domain can still use it.

.. _remove-keycloak-client:

Remove the Keycloak client
--------------------------

The |UASUMM| app signs users in through the Keycloak client ``ucsschool-accounts-ui``
in the ``ucs`` realm.
After you remove the app from every system in the domain,
you can delete that client in the Keycloak administration console at
:samp:`https://ucs-sso-ng.{DOMAIN_NAME}/admin/master/console/`.
Replace ``DOMAIN_NAME`` with the domain name of your UCS domain.
If you have set the Univention Configuration Registry (UCR) variable
:external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
use its value instead of :samp:`ucs-sso-ng.{DOMAIN_NAME}`.
