.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############
Introduction
############

The |UASSA| app lists the users of a |UAS| school
and lets authorized users reset their passwords.
This manual explains how to install, configure, and use the app,
and which roles and permissions decide what each user can see and do.

The :external+uv-nubus-manual:ref:`Guardian <nubus-authorization>`
makes every authorization decision of the app.
It evaluates the policy files that ship with the app,
so a permission depends on the roles of both users
and on how they relate to each other,
for example a teacher and the students in their class,
or a legal guardian and their ward.
For more information about how those policies work and where they come from,
see :external+uv-nubus-manual:ref:`nubus-authorization-policies`.

.. caution::

   The |UASSA| app is a preview.
   Its features and configuration may change incompatibly in future releases.
   Univention supports it on a best-effort basis to help you test it.
   We're happy to receive your feedback.

.. _audience-for-this-manual:

Audience
========

This manual is for administrators who install and operate the |UASSA| app.
It assumes that you can run commands on the command line of a UCS system.
The chapter :ref:`usage` is for the users of the app
and uses only a web browser.
