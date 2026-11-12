.. SPDX-FileCopyrightText: 2023-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############
Introduction
############

The |UASSA| app lists the users of a |UAS| school
and lets authorized users reset other users' passwords.

This manual covers the following topics:

* :ref:`installation` and :ref:`configuration`
* :ref:`usage`
* :ref:`roles-permissions-and-conditions`
* :ref:`troubleshooting` and :ref:`known-issues`

The *Guardian* makes every authorization decision of the app.
It evaluates the policy files that ship with the app.
A permission can depend on the roles of the user requesting an action
and the user whose account the action concerns,
as well as on the relationship between them.
For example, the relationship between a teacher and a student in their class
can affect which permissions the teacher has.
For more information about how those policies work and where they come from,
see :external+uv-nubus-manual:ref:`nubus-authorization-policies`
in :cite:t:`uv-nubus-manual`.

.. caution::

   The |UASSA| app is a preview.
   Its features and configuration may change incompatibly in future releases.
   Univention supports it on a best-effort basis to help you test it.
   We're happy to receive your :ref:`feedback`.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-authorization`
      in :cite:t:`uv-nubus-manual`
      for more information about the *Guardian*.

.. _audience-for-this-manual:

Audience
========

This manual is for administrators who install and operate the |UASSA| app.
It assumes that you have basic knowledge of Nubus for UCS and |UAS| administration
and can use the command line on a Nubus for UCS system.

The chapter :ref:`usage` is for users of the app,
such as school administrators, teachers, and legal guardians.

To use the app, you only need a web browser.

.. _feedback:

Feedback
========

Your feedback on this documentation is welcome.
If you have any comments, suggestions, or corrections,
`submit your feedback <https://www.univention.com/feedback/?ucsschool-accounts=generic>`_
to improve the document.
