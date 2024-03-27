.. Copyright (C) 2023 Univention GmbH
..
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
* The Guardian is installed and configured in the domain.
  The minimum version is 2.0.2 for the authorization API and 2.0.1 for the management API.
  See the :external+uv-guardian-manual:ref:`Guardian Manual <installation>` for further instructions.
* The :external+uv-school-kelvin:doc:`Kelvin Rest API <index>` is installed and configured on the same node.

To install the |UASUMM| from the command line,
run the following command on the backup server:

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

   $ univention-app upgrade ucsschool-user-management
