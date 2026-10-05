.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _installation:

************
Installation
************

This section is for administrators
and covers the installation, upgrade, and removal of the |UASSA| app.

.. _installation-system-requirements:

System requirements
===================

If you install the |UASSA| app and all its dependencies on the
:external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node`,
that system needs at least the following resources:

* 12 GB RAM
* 150 GB disk space

The dependencies are UCS@school, the Guardian, the Kelvin REST API, and Keycloak,
see :ref:`installation_instructions`.

.. _installation_instructions:

Install the app
===============

You can install the |UASSA| app on a
:external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node` or on a
:external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`
that runs Univention Corporate Server (UCS) 5.2-6 with :uv:erratum:`5.2x569` or later.

Your domain must meet the following prerequisites before you install the app:

* :external+uv-school-manual:ref:`UCS@school <introduction>` is installed and configured in the domain.
* The Guardian (``univention-guardian``) is installed and configured
  on the same system as the |UASSA| app.
  For more information, see :external+uv-ucs-operation:ref:`iam-authorization-engine-install`.
* The :external+uv-school-kelvin:doc:`Kelvin REST API <index>` in version 4.1.0 or later
  is installed and configured
  on the same system as the |UASSA| app.
  The installation and the update of the |UASSA| app abort otherwise.
* Keycloak is installed and configured in the domain as the identity provider.
  For more information about installing Keycloak,
  see the :external+uv-keycloak:ref:`Univention Keycloak app documentation <app-installation>`.

To install the |UASSA| app from the command line,
run the following command:

.. code-block:: console
   :caption: Install the |UASSA| app from the command line

   $ univention-app install ucsschool-accounts

After the installation,
users reach the app through the
:external+uv-ucs-manual:ref:`Univention Portal <central-portal>`.
To choose who sees the portal tile, see :ref:`configuration-portal-tile`.
The tile opens the app on the first system in the domain that you install it on.
To point it to another system, see :ref:`configuration-portal-tile-link`.

.. _upgrade:

Upgrade the app
===============

To upgrade the |UASSA| app to a later version,
run the following command:

.. code-block:: console
   :caption: Upgrade the |UASSA| app from the command line

   $ univention-app upgrade ucsschool-accounts

.. _removal:

Remove the app
==============

To remove the |UASSA| app from a system,
run the following command:

.. code-block:: console
   :caption: Remove the |UASSA| app from the command line

   $ univention-app remove ucsschool-accounts

The removal deletes the portal tile and the policies of the app.
It deletes the tile even if the app still runs on other systems,
see :ref:`known-issue-removal-deletes-tile`.
It keeps the Keycloak client,
because other systems in the domain can still use it.

.. _remove-keycloak-client:

Remove the Keycloak client
--------------------------

The |UASSA| app signs users in through the Keycloak client ``ucsschool-accounts-ui``
in the ``ucs`` realm.
After you remove the app from every system in the domain,
you can delete that client in the Keycloak administration console at
:samp:`https://ucs-sso-ng.{DOMAIN_NAME}/admin/master/console/`.
Replace ``DOMAIN_NAME`` with the domain name of your UCS domain.
If you have set the Univention Configuration Registry (UCR) variable
:external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
use its value instead of :samp:`ucs-sso-ng.{DOMAIN_NAME}`.
