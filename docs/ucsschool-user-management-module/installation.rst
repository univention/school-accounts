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

Before installing the User Management module, the following prerequisites are needed:

* :external+uv-school-manual:ref:`UCS@school <introduction>` is installed and configured in the domain.
* The Guardian (``univention-guardian``) is installed and configured
  on the same system as the |UASUMM|.
  See :external+uv-ucs-operation:ref:`iam-authorization-engine-install`
  for further instructions.
* The :external+uv-school-kelvin:doc:`Kelvin Rest API <index>` is installed and configured
  in the domain. By default, the |UASUMM| expects the Kelvin REST API on the same system.
  If the Kelvin REST API runs on a different system,
  set the :envvar:`ucsschool-user-management/kelvin/url` variable to its URL.
* Keycloak is installed and configured in the domain as the identity provider.
  For more information about installing Keycloak,
  see the :external+uv-keycloak:ref:`Univention Keycloak app documentation <app-installation>`.

To install the |UASUMM| from the command line,
run the following command:

.. code-block:: bash
   :caption: Install |UASUMM| apps from command line

   $ univention-app install \
       ucsschool-user-management

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
       ucsschool-user-management


Removing the UCS\@school User Management module
===============================================

To remove the UCS\@school User Management module from the server, use the command ``univention-app remove``:

.. code-block:: bash
   :caption: Remove UCS\@school User Management module apps from command line

   $ univention-app remove \
       ucsschool-user-management

Keycloak clients
----------------

The Keycloak client won't be removed automatically. If you want to remove it, you can do it manually in the Keycloak admin interface. The interface is reachable via ``https://ucs-sso-ng.<FQDN>/admin/master/console/``, where `FQDN` is the fully qualified domain name of the system the `user-management` module is installed on.

The client name is:

- ``ucsschool-user-management-ui``
