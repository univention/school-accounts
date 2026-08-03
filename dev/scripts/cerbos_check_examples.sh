#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Example `CheckResources` calls against a local Cerbos server, one per
# resource_policy rule family. Start the server first with
# `./dev/dev_run.sh task cerbos-server`, then run this script from the repo
# root (or copy/adapt individual curl calls to try your own scenarios).

set -e

CERBOS_URL="http://localhost:3592/api/check/resources"

check() {
    local description="$1"
    local payload="$2"
    echo "=== $description ==="
    curl -s "$CERBOS_URL" -H "Content-Type: application/json" -d "$payload" | python3 -m json.tool
    echo
    return 0
}

check "self: alice reads her own data, not someone else's" '{
  "requestId": "self-read",
  "principal": {"id": "alice", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "student", "context": "school1"}], "school_classes": {}}},
  "resources": [
    {"resource": {"id": "alice", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "student", "context": "school1"}], "school_classes": {}}}}, "actions": ["read-first_name", "read-disabled"]},
    {"resource": {"id": "someone_else", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "student", "context": "school2"}], "school_classes": {}}}}, "actions": ["read-first_name"]}
  ]
}'

check "teacher: bob (class 1a) reads/resets a student in his class, not another class" '{
  "requestId": "teacher-class-scope",
  "principal": {"id": "bob", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "teacher", "context": "school1"}], "school_classes": {"school1": ["1a"]}}},
  "resources": [
    {"resource": {"id": "student1", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "student", "context": "school1"}], "school_classes": {"school1": ["1a"]}}}}, "actions": ["read-first_name", "write-password"]},
    {"resource": {"id": "student2", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "student", "context": "school1"}], "school_classes": {"school1": ["1b"]}}}}, "actions": ["read-first_name", "write-password"]}
  ]
}'

check "school_admin: dave resets passwords in his school, except for another school_admin" '{
  "requestId": "school-admin-reset",
  "principal": {"id": "dave", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "school_admin", "context": "school1"}], "school_classes": {}}},
  "resources": [
    {"resource": {"id": "teacher1", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "teacher", "context": "school1"}], "school_classes": {}}}}, "actions": ["write-password"]},
    {"resource": {"id": "admin2", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "school_admin", "context": "school1"}], "school_classes": {}}}}, "actions": ["write-password"]}
  ]
}'

check "staff: grace reads the same fields as a teacher, but only of other staff, and can't reset passwords" '{
  "requestId": "staff-parity",
  "principal": {"id": "grace", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "staff", "context": "school1"}], "school_classes": {}}},
  "resources": [
    {"resource": {"id": "staff1", "kind": "ucsschool:user", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "staff", "context": "school1"}], "school_classes": {}}}}, "actions": ["read-birthday", "write-password"]}
  ]
}'

# Non-user targets carry a synthesised role as well as their school: the BFF's
# _target_object_to_guardian_object builds school_class:school:<school>,
# workgroup:school:<school> and school:school:<id>. The school_admin filter
# rules match against those roles, so omitting them here would make them look
# broken.
check "class filter: bob (member of 1a) can filter by his class, not another one" '{
  "requestId": "class-filter-member",
  "principal": {"id": "bob", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [], "school_classes": {"school1": ["1a"]}}},
  "resources": [
    {"resource": {"id": "1a", "kind": "ucsschool:class", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school1", "cerbos_roles": [{"name": "school_class", "context": "school1"}]}}}, "actions": ["use-as-filter"]},
    {"resource": {"id": "1b", "kind": "ucsschool:class", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school1", "cerbos_roles": [{"name": "school_class", "context": "school1"}]}}}, "actions": ["use-as-filter"]}
  ]
}'

check "class filter: dave (school_admin, member of no class) can filter any class in his school" '{
  "requestId": "class-filter-school-admin",
  "principal": {"id": "dave", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "school_admin", "context": "school1"}], "school_classes": {}}},
  "resources": [
    {"resource": {"id": "1a", "kind": "ucsschool:class", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school1", "cerbos_roles": [{"name": "school_class", "context": "school1"}]}}}, "actions": ["use-as-filter"]},
    {"resource": {"id": "2a", "kind": "ucsschool:class", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school2", "cerbos_roles": [{"name": "school_class", "context": "school2"}]}}}, "actions": ["use-as-filter"]}
  ]
}'

# The school_admin case for work groups mirrors the class one above.
check "work group filter: bob can filter by the work group he belongs to, not another one" '{
  "requestId": "work-group-filter",
  "principal": {"id": "bob", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [], "work_groups": {"school1": ["chess-club"]}}},
  "resources": [
    {"resource": {"id": "chess-club", "kind": "ucsschool:workgroup", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school1", "cerbos_roles": [{"name": "workgroup", "context": "school1"}]}}}, "actions": ["use-as-filter"]},
    {"resource": {"id": "art-club", "kind": "ucsschool:workgroup", "attr": {"app_name": "ucsschool-user-management", "old": {"school": "school1", "cerbos_roles": [{"name": "workgroup", "context": "school1"}]}}}, "actions": ["use-as-filter"]}
  ]
}'

check "school filter: bob can filter by the school he is enrolled in, not another one" '{
  "requestId": "school-filter",
  "principal": {"id": "bob", "roles": ["ucsschool:user"], "attr": {"cerbos_roles": [{"name": "student", "context": "school1"}], "schools": ["school1"]}},
  "resources": [
    {"resource": {"id": "school1", "kind": "ucsschool:school", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "school", "context": "school1"}]}}}, "actions": ["use-as-filter"]},
    {"resource": {"id": "school2", "kind": "ucsschool:school", "attr": {"app_name": "ucsschool-user-management", "old": {"cerbos_roles": [{"name": "school", "context": "school2"}]}}}, "actions": ["use-as-filter"]}
  ]
}'
