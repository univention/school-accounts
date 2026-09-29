# shellcheck shell=bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Inlined into preinst by generate-preinst; kept as its own file so the bats
# tests can source it without running the rest of the preinst.

# Minimum version of the Kelvin REST API app that must be installed on this
# host.
MIN_KELVIN_VERSION="4.1.0"

# check_kelvin_version [min_version]
#
# 'RequiredApps' in the ini only makes the App Center check that Kelvin is
# installed on this host, not which version. This reads the installed version
# from the UCR variables the App Center itself keeps per app and consults in
# App.is_installed(): appcenter/apps/<id>/status is "installed" (or "stalled")
# and appcenter/apps/<id>/version holds the installed version.
#
# The comparison reuses the App Center's own comparator (LooseVersion), the one
# it uses for RequiredAppVersionUpgrade; there is no 'univention-app'
# subcommand that compares two version strings.
#
# Branch test versions of the app ("0.0.0-<suffix>") always count as recent
# enough, so the app can be installed next to a Kelvin branch build.
#
# Arguments:
#   $1 - minimum version to require (defaults to $MIN_KELVIN_VERSION)
#
# Returns:
#   0 - a Kelvin >= the minimum, or a branch test version, is installed on this
#       host
#   1 - Kelvin is not installed on this host
#   2 - Kelvin is installed on this host, but its version is too old
check_kelvin_version() {
    local min_version="${1:-$MIN_KELVIN_VERSION}"

    local status version
    status="$(ucr get appcenter/apps/ucsschool-kelvin-rest-api/status)"
    version="$(ucr get appcenter/apps/ucsschool-kelvin-rest-api/version)"

    case "$status" in
        installed|stalled) ;;
        *) return 1 ;;
    esac
    if [[ -z "$version" ]]; then
        return 1
    fi

    if python3 -c '
import sys

from univention.appcenter.app import LooseVersion

version, required = sys.argv[1:]
sys.exit(0 if version.startswith("0.0.0-") or LooseVersion(version) >= LooseVersion(required) else 1)
' "$version" "$min_version"; then
        return 0
    fi

    return 2
}
