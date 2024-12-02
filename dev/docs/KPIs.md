<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

# User Management KPIs

Those KPIs are defined such that they are reached for 95% of all requests.
These KPIs expect the school server (running Kelvin and UDM REST) to have at least
[the minimal system requirements](https://docs.software-univention.de/ucsschool-scenarios/5.0/de/network-and-hardware.html#infrastructure-and-hardware-requirements-servers-primary-directory-node)

Prerequisites:

- The domain has 10 schools with 5000 users each.
  - Following [OECD statistics](https://www.oecd.org/en/data/indicators/students-per-teaching-staff.html) that
  should be about one teacher per 15 students, so 312 teachers to 4688 students.
- Each school class is not bigger than 31 members.
- Each teacher is in 5 school classes.
- Each school class has a maximum of 7 teachers.
- A third of the students are in 2 school classes.
- Each school has 5 school admins.

## Search

The time it takes for a user clicking the search button, until the first results
are presented in the table on the UI.

- [A1] (500ms) A domain admin searches for any users with a variety of search filters.
- [A2] (500ms) A school admin is searching for users in their school.
- [A3] (500ms) A teacher is searching for students in their classes.
- [A4] (500ms) A student is searching for users (to find their own object).
- [A5] (1s)    All school admins are searching for users in their schools.
- [A6] (1s)    100 teachers search for students in their classes.
- [A7] (1s)    100 students search for users (to find their own object).

## User Creation

- [B1] (1s) A domain admin creates a new user.
- [B2] (1s) A school admin creates a new user.
- [B3] (2s) All school admins create students in their schools.

## User Modification

- [C1] (1s) A domain admin modifies any values on a user.
- [C2] (1s) A school admin modifies any values on a user.
- [C3] (1s) A teacher changes the password of one of their students.
- [C4] (1s) A student changes their own password.
- [C5] (2s) 100 teachers change the passwords of their students.
- [C6] (2s) 100 students change their own password.

## Group Creation

- [D1] (1s) A domain admin creates a group.
- [D2] (1s) A school admin creates a group.
- [D3] (1s) A teacher creates a work group.
- [D4] (2s) All school admins create groups in their schools.
- [D5] (2s) 100 teachers create work groups in their schools.

## Group Modification

- [E1] (1s) A domain admin modifies any values on a group.
- [E2] (1s) A school admin modifies any values on a group.
- [E3] (1s) A teacher modifies any values on a group.
- [E4] (2s) All school admins modify any values of groups.
- [E5] (2s) 100 teachers modify work groups.

## Mass Actions

- [F1] (1s) A teacher resets the password of a student.
- [F2] (4.5s) A teacher resets the password of 30 students.
- [F3] (4.5s) A school admin resets the password of 30 users.
- [F4] (6s) 100 teachers reset the password of 30 students each.
