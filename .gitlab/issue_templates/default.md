<!--
Copyright (C) 2023 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

/label ~"App::RAM"
/label ~"Team::UCS@school"
/label ~"Status::New"

## Accounting

- Univention GmbH (424)
- Development: TBD

## Story

As a \<role\>
I can \<capability\>,
so that \<receive benefit\>.

## Context/description

A little context to the issue. Where does the task come from, what is needed for implementation. Everything which is important but doesn't fit the user story syntax can be written down here.

A user story should be self-contained and provide value when shipped. It should also contain a "single source of truth".

Additional points:

- If possible, list implementation constraints here (e.g. after a refinement)
- Separation to other user stories
- Desired artifacts (package, documentation, release, etc.)
- Specific requirements regarding documentation if required
- For UI-heavy stories: Mockups, wireframes, storyboards, etc.

## Acceptance criteria & steps for reproduction

- [ ]
- [ ]

- [ ] All changed lines are covered by a unit test, if possible.
  - [ ] Happy case.
  - [ ] Unhappy case (errors and edge cases).
- [ ] There is at least one end to end test that covers the changed lines.
- [ ] Evaluate performance of the change.
  - [ ] Read the parent epic and verify performance requirements.
  - [ ] If necessary, performance tests exist. See [Performance commitment](https://git.knut.univention.de/univention/internal/decision-records/-/blob/main/ucsschool/0008-performance-commitment.md)
  - [ ] If there are no specific performance requirements, improve or at least avoid worsening existing performance, if possible.
  - [ ] Document reasons for worse performance in the code and on the ticket, if applicable.

If the changes affect security features such as authentication or authorization:

- [ ] The affected security feature has a dedicated end to end integration test.

## QA

Please explicitly check off all steps performed in the QA process.
If certain steps are not applicable, please use ~strikethrough~ and note why these steps were not performed.

## Technical QA

Technical QA is focused on the code quality and basic runability of the code.
All Technical QA steps should also be performed by the implementer before handing over to QA.

- [ ] Code review on the merge request:
  - [ ] Changelogs are present (`README_UPDATE_*`-files and `docs/ucsschool-user-management-module/changelog.rst`)
  - [ ] Tests sufficiently cover the changed lines of code.
- [ ] Pipelines pass.
- [ ] App installation succeeds on a test VM.
- [ ] App update succeeds on a test VM.
- [ ] Basic smoke test:
  - [ ] If a service was changed (added, modified) the service is running after the installation and restarting works without problems. If it was removed, it must not be running anymore.
  - [ ] The app user-management are running.
  - [ ] Log in to the user-management ui as `alex.admin` and try to list and modify users.
  - [ ] New Cron jobs, listeners, etc. actually run.
  - [ ] Permissions are checked for new files (e.g., a script must be executable, right ownership of directories and created files in regard to data security).
  - [ ] New tests pass.

## Functional QA

Functional QA focuses on the user using the User Management UI.

- [ ] Post a QA plan on the gitlab issue of what will be tested:
  - [ ] Include a happy path and multiple non-happy path scenarios.
  - [ ] All software components that might be affected, not just the code that was changed.
  - [ ] Verify that examples in the documentation of the changed components still work.
  - [ ] Agree on QA plan with implementer.
- [ ] Manually run the QA plan
- [ ] Document all reproduction steps of the QA plan:
  - [ ] What commands were used to test?
  - [ ] What input values were used to test? Why were these values chosen?
  - [ ] Get creative and try to break the implementation
  - [ ] If possible, take screenshots before and afterward the fix.

## Before merge

 No merge without:

- [ ] Verify again that the integration tests pass in the pipeline.
- [ ] Gitlab integration tests pass.

## After Merge

- [ ] Gitlab integration tests pass after merge in main.
- [ ] Installation succeeds on a test VM.
- [ ] Smoke test installation: see section Technical QA.
- [ ] Gitlab issue is linked to release issue.
