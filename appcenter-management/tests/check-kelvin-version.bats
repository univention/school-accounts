#!/usr/bin/env bats

# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

setup() {
  export PATH="$BATS_TEST_DIRNAME/mocks:$PATH"

  export MOCK_CALLS="$BATS_TEST_TMPDIR/calls.log"
  : > "$MOCK_CALLS"

  # The check imports univention.appcenter.app.LooseVersion, which only exists
  # on a UCS docker host. Put a faithful stub on PYTHONPATH.
  export PYTHONPATH="$BATS_TEST_DIRNAME/stubs${PYTHONPATH:+:$PYTHONPATH}"

  export MOCK_LDAP_OUTPUT=""

  source "$BATS_TEST_DIRNAME/../templates/check-kelvin-version.sh"
}

# Emit what `univention-ldapsearch -LLL ... univentionAppVersion` would for the
# given Kelvin versions (one arg per installed server object).
ldap_output_for_versions() {
  local out="" v
  for v in "$@"; do
    out+="univentionAppVersion: ${v}"$'\n'
  done
  printf '%s' "$out"
}

# Generate the preinst from a copy of the sources, so the test neither
# depends on nor overwrites a preinst in the working tree.
generate_preinst() {
  local build_dir="$BATS_TEST_TMPDIR/build"
  mkdir -p "$build_dir"
  cp -r "$BATS_TEST_DIRNAME/../templates" "$BATS_TEST_DIRNAME/../files" "$BATS_TEST_DIRNAME/../scripts" "$build_dir"
  (cd "$build_dir" && ./scripts/generate-preinst)
  printf '%s' "$build_dir/preinst"
}

@test "check_kelvin_version: not installed -> returns 1" {
  run check_kelvin_version
  [ "$status" -eq 1 ]

  grep -q "univentionObjectType=appcenter/app" "$MOCK_CALLS"
  grep -q "univentionAppID=ucsschool-kelvin-rest-api_\*" "$MOCK_CALLS"
  grep -q "univentionAppInstalledOnServer=\*" "$MOCK_CALLS"
}

@test "check_kelvin_version: exactly the minimum -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.1.0)"

  run check_kelvin_version
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: only an older version -> returns 2" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.0.2)"

  run check_kelvin_version
  [ "$status" -eq 2 ]
}

@test "check_kelvin_version: 4.10.0 beats 4.2.0 (numeric, not lexical) -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.10.0)"

  run check_kelvin_version 4.2.0
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: newer major -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 5.0.0)"

  run check_kelvin_version
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: several servers, one recent enough -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.0.2 4.1.1)"

  run check_kelvin_version
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: several servers, all too old -> returns 2" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 3.3.1 4.0.2)"

  run check_kelvin_version
  [ "$status" -eq 2 ]
}

@test "check_kelvin_version: honours an explicit minimum argument" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.2.0)"

  run check_kelvin_version 5.0.0
  [ "$status" -eq 2 ]

  run check_kelvin_version 4.1.0
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: branch test version -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 0.0.0-feat-ucs-5-3)"

  run check_kelvin_version
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: merge request test version -> returns 0" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions '0.0.0-MR-1234-univention/dev/education/ucsschool-kelvin-rest-api!567')"

  run check_kelvin_version
  [ "$status" -eq 0 ]
}

@test "check_kelvin_version: 0.0.0 without suffix is not a test version -> returns 2" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 0.0.0)"

  run check_kelvin_version
  [ "$status" -eq 2 ]
}

@test "check_kelvin_version: default minimum is 4.1.0" {
  [ "$MIN_KELVIN_VERSION" = "4.1.0" ]
}

@test "preinst: too old Kelvin fails with a message in the error file" {
  export MOCK_LDAP_OUTPUT="$(ldap_output_for_versions 4.0.2)"
  preinst="$(generate_preinst)"

  run bash "$preinst" --version 1.0.0 --error-file "$BATS_TEST_TMPDIR/error"
  [ "$status" -eq 1 ]
  grep -q "in at least version 4.1.0" "$BATS_TEST_TMPDIR/error"
}

@test "preinst: missing Kelvin fails with a message in the error file" {
  preinst="$(generate_preinst)"

  run bash "$preinst" --error-file "$BATS_TEST_TMPDIR/error"
  [ "$status" -eq 1 ]
  grep -q "requires the 'UCS@school Kelvin REST API' app to be installed" "$BATS_TEST_TMPDIR/error"
}
