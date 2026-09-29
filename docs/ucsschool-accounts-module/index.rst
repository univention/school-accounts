.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############
Introduction
############

Welcome to the School Accounts manual.
It explains how to use the module to manage users and how to modify roles
and permissions through the :external+uv-nubus-manual:ref:`Guardian <nubus-authorization>`.

Historically, UCS\@school user roles were limited to a few roles, such as
teachers and students, and the permissions were hard-coded into the
applications. This made it impossible to change the permissions for
these roles, or to add new roles.

The Guardian is a new system for managing roles and permissions. And it's
what the School Accounts app uses.

Now you can create new roles, and assign permissions to them. For example,
you can create a role “legal guardian” and assign the permissions to view
only the data of the children they are responsible for.
Roles and permissions live in policy files that the Guardian evaluates.
For how those policies work and where they come from,
see :external+uv-nubus-manual:ref:`nubus-authorization-policies`.

.. _audience-for-this-manual:

The School Accounts manual addresses the following audiences:

* Administrators

.. caution::

   The current state of the project is a technical preview. It is not supported yet.

.. _guardian-administrators-audience:

Administrators
==============

A School Accounts administrator in the context of this manual
is a superuser who administers the School Accounts app, including
the Guardian roles and permissions if desired.

This manual doesn't assume any specific technical knowledge
for administrators of the School Accounts app.
When possible, all instructions use a web browser.
