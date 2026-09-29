.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############
Introduction
############

The School Accounts app lists the users of a UCS\@school school
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

   The School Accounts app is a technical preview.
   Univention doesn't support it.

.. _audience-for-this-manual:

Audience
========

This manual is for administrators who install and operate the School Accounts app.
It doesn't assume any specific technical knowledge.
When possible, all instructions use a web browser.
