.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _known-issues:

************
Known issues
************

This section lists the known issues of the |UASUMM| app.

.. _known-issue-removal-deletes-tile:

Removing the app from one system deletes the portal tile
========================================================

The domain has one |UASUMM| portal tile for all systems that run the app.
Removing the app from any of these systems deletes that tile,
even if the app still runs on other systems.
Users then can't open the app from the portal anymore.
