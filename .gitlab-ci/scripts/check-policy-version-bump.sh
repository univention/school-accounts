#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Fail when a shipped Cerbos policy changed without VERSION in
# appcenter-management/inst being increased.
#
# An edited policy only reaches an installed system once VERSION is bumped:
# joinscript_init skips the join script unless VERSION increased, and
# ucs_registerLDAPExtension skips overwriting the registered bundle unless
# --packageversion (also VERSION) increased. Forgetting the bump fails silently
# on the target system, which is what this check exists to prevent.
#
# *_test.yaml files are filtered out by generate-preinst and never ship, so a
# test-only change does not require a bump.
#
# Usage: check-policy-version-bump.sh [<base-ref>]
#   <base-ref> defaults to $CI_MERGE_REQUEST_DIFF_BASE_SHA (set in GitLab MR
#   pipelines). Locally, pass the branch you are merging into, e.g.
#     .gitlab-ci/scripts/check-policy-version-bump.sh origin/main

set -euo pipefail

POLICIES_DIR="appcenter-management/files/policies"
INST="appcenter-management/inst"

base="${1:-${CI_MERGE_REQUEST_DIFF_BASE_SHA:-}}"
if [[ -z "$base" ]]; then
    echo "ERROR: no base ref given and CI_MERGE_REQUEST_DIFF_BASE_SHA is unset." >&2
    echo "Usage: $0 [<base-ref>]" >&2
    exit 2
fi

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is not available in this image." >&2
    echo "Pin an image that ships git (e.g. \$DEV_IMAGE_TAG) for this job." >&2
    exit 2
fi

cd "$(git rev-parse --show-toplevel)"

read_version() {
    sed -n 's/^VERSION=\([0-9][0-9]*\).*/\1/p' | head -1
    return 0
}

# Only files that actually ship in the bundle force a bump.
shipped="$(git diff --name-only "$base" HEAD -- "$POLICIES_DIR" | { grep -v '_test\.yaml$' || true; })"
if [[ -z "$shipped" ]]; then
    echo "Only *_test.yaml policy files changed. These are filtered out by"
    echo "generate-preinst and never ship, so no VERSION bump is needed."
    exit 0
fi

base_inst="$(git show "$base:$INST" 2>/dev/null || true)"
if [[ -z "$base_inst" ]]; then
    echo "$INST not present at $base; nothing to compare against."
    exit 0
fi

base_version="$(printf '%s\n' "$base_inst" | read_version)"
head_version="$(read_version < "$INST")"
if [[ -z "$base_version" || -z "$head_version" ]]; then
    echo "ERROR: could not parse VERSION from $INST" >&2
    echo "  base='$base_version' head='$head_version'" >&2
    echo "Has the 'VERSION=<n>' line changed shape?" >&2
    exit 1
fi

echo "Shipped policy files changed:"
printf '%s\n' "$shipped" | sed 's/^/  /'
echo "VERSION: $base_version ($base) -> $head_version (HEAD)"

if [[ "$head_version" -le "$base_version" ]]; then
    echo >&2
    echo "ERROR: shipped Cerbos policies changed, but VERSION in $INST was not increased." >&2
    echo "Bump it above $base_version so the join script re-runs and" >&2
    echo "ucs_registerLDAPExtension overwrites the registered policy bundle." >&2
    exit 1
fi

echo "OK: VERSION was bumped."
