.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _installation:

************
Installation
************

This section is for administrators
and covers the installation of the |UASUMM| on UCS systems.
If you're upgrading the |UASUMM| to a new version, refer to the upgrade guide :ref:`upgrade`.

.. _installation_instructions:

Installation instructions
=========================

The |UASUMM| can be installed on a
:external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node` or on a
:external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`.

Before installing the School Accounts app, the following prerequisites are needed:

* :external+uv-school-manual:ref:`UCS@school <introduction>` is installed and configured in the domain.
* The Guardian (``univention-guardian``) is installed and configured
  on the same system as the |UASUMM|.
  See :external+uv-ucs-operation:ref:`iam-authorization-engine-install`
  for further instructions.
* The :external+uv-school-kelvin:doc:`Kelvin Rest API <index>` in version 4.1.0 or later
  is installed and configured
  on the same system as the |UASUMM|.
  The installation and the update of the |UASUMM| abort otherwise.
* Keycloak is installed and configured in the domain as the identity provider.
  For more information about installing Keycloak,
  see the :external+uv-keycloak:ref:`Univention Keycloak app documentation <app-installation>`.

To install the |UASUMM| from the command line,
run the following command:

.. code-block:: bash
   :caption: Install |UASUMM| apps from command line

   $ univention-app install \
       ucsschool-accounts

You have completed the |UASUMM| setup.
You can reach the module from the
:external+uv-ucs-manual:ref:`Univention Portal <central-portal>`.

.. _upgrade:

Upgrading the |UASUMM|
================================================

For minor and patch level version changes, use the command ``univention-app upgrade``:

.. code-block:: bash
   :caption: Install |UASUMM| apps from command line

   $ univention-app upgrade \
       ucsschool-accounts


Removing the School Accounts app
===============================================

To remove the School Accounts app from the server, use the command ``univention-app remove``:

.. code-block:: bash
   :caption: Remove School Accounts app from command line

   $ univention-app remove \
       ucsschool-accounts

Keycloak clients
----------------

The Keycloak client won't be removed automatically. If you want to remove it, you can do it manually in the Keycloak admin interface. The interface is reachable via ``https://ucs-sso-ng.<FQDN>/admin/master/console/``, where `FQDN` is the fully qualified domain name of the system the ``ucsschool-accounts`` app is installed on.

The client name is:

- ``ucsschool-accounts-ui``
