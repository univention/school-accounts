.. Copyright (C) 2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

############
Introduction
############

Welcome to the UCS\@school User Management manual.
It explains how to use the module to manage users and how to modify roles
and permissions through the :external+uv-guardian-manual:ref:`Guardian <what-is-the-guardian>`.

Historically, UCS\@school user roles were limited to a few roles, such as
teachers and students, and the permissions were hard-coded into the
applications. This made it impossible to change the permissions for
these roles, or to add new roles.

The Guardian is a new system for managing roles and permissions. And it's
what the UCS\@school User Management module uses.

Now you can create new roles, and assign permissions to them. For example,
you can create a role “legal guardian” and assign the permissions to view
only the data of the children they are responsible for. You can find more
details on the process in the :external+uv-guardian-manual:ref:`Guardian manual <management-ui>` .

.. _audience-for-this-manual:

The UCS\@school User Management manual addresses the following audiences:

* Administrators

.. caution::

   The current state of the project is a technical preview. It is not supported yet.

.. _guardian-administrators-audience:

Administrators
==============

A UCS\@school User Management administrator in the context of this manual
is a superuser who administers the UCS\@school User Management module, including
the Guardian roles and permissions if desired.

This manual doesn't assume any specific technical knowledge
for administrators of the UCS\@school User Management.
When possible, all instructions use a web browser.
