.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _installation:

************
Installation
************

This section is for administrators
and covers the installation of the UCS\@school User Management module on UCS systems.
If you're upgrading the UCS\@school User Management module to a new version, refer to the upgrade guide :ref:`upgrade`.

.. _installation_instructions:

Installation instructions
=========================

This section describes the installation of the UCS\@school User Management module on a
:external+uv-ucs-manual:ref:`domain-ldap-primary-directory-node` or a
:external+uv-ucs-manual:ref:`domain-ldap-backup-directory-node`.

UCS\@school User Management module administrators
install the UCS\@school User Management module from the Univention App Center.
A prerequisite for using the UCS\@school User Management module is a working
Guardian and UCS\@school installation in the UCS domain.
For information about how to install and configure the Guardian in a UCS,
refer to
`Guardian Manual <https://docs.software-univention.de/guardian-manual/latest/installation.html>`_.

To install all required components, run the following command:

.. code-block:: bash
   :caption: Install UCS\@school User Management module apps from command line

   $ univention-app install \
       ucsschool-user-management


You have completed the UCS\@school User Management module setup.
You can reach the module from the
:external+uv-ucs-manual:ref:`Univention Portal <central-portal>`.

.. _upgrade:

Upgrading the UCS\@school User Management module
================================================

For minor and patch level version changes, use the command ``univention-app upgrade``:

.. code-block:: bash
   :caption: Install UCS\@school User Management module apps from command line

   $ univention-app upgrade \
       ucsschool-user-management
