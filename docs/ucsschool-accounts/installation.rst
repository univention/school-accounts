.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _installation:

************
Installation
************

Administrators can use this section to install, upgrade, and remove the |UASSA| app.

.. _installation-requirements:

System requirements
===================

If you install the |UASSA| app and all its dependencies on the
:external+uv-ucs-operation:term:`Primary Directory Node`,
that system needs at least the following resources:

* 12 GB of RAM
* 150 GB of disk space

The |UASSA| app has the following dependencies:

* |UAS|
* the *Guardian*
* the Kelvin REST API
* Keycloak

You can install the |UASSA| app on a
:external+uv-ucs-operation:term:`Primary Directory Node` or on a
:external+uv-ucs-operation:term:`Backup Directory Node`
that runs Nubus for Univention Corporate Server (UCS) 5.2-7 with :uv:erratum:`5.2x701` or later.
The systems that serve the Univention Portal need this erratum as well,
because without it Firefox can't save the CSV export of the user list.

.. _installation-prerequisites:

Prerequisites
=============

Your domain must meet the following prerequisites before you install the app:

* You have the |UAS| app installed
  and configured in the domain.
  For more information,
  see :external+uv-school-manual:ref:`introduction`
  in :cite:t:`uv-school-manual`.

* You have the authorization engine *Guardian* installed
  and configured on the same system as the |UASSA| app.
  For more information,
  see :external+uv-ucs-operation:ref:`iam-authorization-engine-install`
  in :cite:t:`uv-ucs-operation`.

* You have the :external+uv-school-kelvin:doc:`Kelvin REST API <index>` 4.1.0 or later
  installed and configured on the same system as the |UASSA| app.
  Otherwise, the installation and update of the |UASSA| app stop.

* You have the *Keycloak* app installed and configured in the domain as the identity provider.
  For more information about installing Keycloak,
  see :external+uv-keycloak:ref:`app-installation`
  in :cite:t:`uv-keycloak`.

.. _installation-app-install:

Install the app
===============

To install the |UASSA| app from the command line,
run the command in :numref:`installation-app-install-listing`.

After the installation,
users can access the app through the *Univention Portal*.
If a user doesn't see the portal tile,
see :ref:`troubleshooting-portal-tile`.

For information about how to configure which users see the portal tile,
see :ref:`configuration-portal-tile`.

The tile opens the app on the first system in the domain
that you install the app on.
For information about how to point the tile to another system,
see :ref:`configuration-portal-tile-link`.

.. code-block:: console
   :caption: Install the |UASSA| app from the command line
   :name: installation-app-install-listing

   $ univention-app install ucsschool-accounts

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal`
      in :cite:t:`uv-nubus-manual`
      for information about *Univention Portal*.

.. _installation-app-upgrade:

Upgrade the app
===============

To upgrade the |UASSA| app to a later version,
run the command in :numref:`installation-app-upgrade-listing`.

.. code-block:: console
   :caption: Upgrade the |UASSA| app from the command line
   :name: installation-app-upgrade-listing

   $ univention-app upgrade ucsschool-accounts

.. _installation-app-remove:

Remove the app
==============

To remove the |UASSA| app from a system,
run the command in :numref:`installation-app-remove-listing`.

Removing the |UASSA| app deletes the portal tile
and the policies of the app.
It deletes the tile even if the app still runs on other systems.
See :ref:`known-issue-removal-deletes-tile`.

The app removal doesn't remove the Keycloak client,
because other systems in the domain can still use it.

.. code-block:: console
   :caption: Remove the |UASSA| app from the command line
   :name: installation-app-remove-listing

   $ univention-app remove ucsschool-accounts

.. _installation-remove-keycloak-client:

Remove the Keycloak client
--------------------------

The |UASSA| app signs users in through the Keycloak client ``ucsschool-accounts-ui``
in the ``ucs`` realm.

After you remove the app from every system in the domain,
you can delete that client in the Keycloak administration console at
:samp:`https://ucs-sso-ng.{DOMAIN_NAME}/admin/master/console/`.
Replace :samp:`{DOMAIN_NAME}` with the domain name of your UCS domain.

If you set the Univention Configuration Registry (UCR) variable
:external+uv-keycloak:envvar:`keycloak/server/sso/fqdn`,
use its value instead of :samp:`ucs-sso-ng.{DOMAIN_NAME}`.

.. seealso::

   :external+uv-keycloak:ref:`ad-hoc-provisioning-admin-console-sign-in`
      in :cite:t:`uv-keycloak`
      for information about how to sign in to *Keycloak Admin Console*.
