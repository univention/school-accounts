.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _known-issues:

************
Known issues
************

This section lists the known issues with the |UASSA| app.

.. _known-issue-removal-deletes-tile:

Removing the app from one system deletes the portal tile
========================================================

The domain has one |UASSA| portal tile for all systems that run the app.
Removing the app from any of these systems deletes that tile,
even if the app still runs on other systems.
Users then can't open the app from the portal anymore.

To restore the tile,
run the join script of the app again
on one of the systems where the app still runs.
The join script recreates the tile with its default settings.
It also restores the policies of the app,
which the removal deletes, as well.
The recreated tile links to the system where you run the join script.

Run the command in :numref:`known-issue-removal-deletes-tile-listing`
as ``root`` on that system.
The command asks for the username and password of a domain administrator.

.. code-block:: console
   :caption: Restore the portal tile and the policies of the app
   :name: known-issue-removal-deletes-tile-listing

   $ univention-run-join-scripts --ask-pass --force \
       --run-scripts 50ucsschool-accounts.inst

The recreated tile doesn't keep changes that you made to the previous tile.
Reapply your changes to the recreated tile,
for example, as described in :ref:`configuration-portal-tile`.
If the portal and the app use different origins,
check the app setting :envvar:`ucsschool-accounts/frame-ancestors`,
as described in :ref:`configuration-portal-tile-link`.
Verify that the tile appears in the portal and opens the app.
