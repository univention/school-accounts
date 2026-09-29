# shellcheck shell=bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Inlined into preinst by generate-preinst; kept as its own file so the bats
# tests can source it without running the rest of the preinst.

# Minimum version of the Kelvin REST API app that must be installed somewhere
# in the domain.
MIN_KELVIN_VERSION="4.1.0"

# check_kelvin_version [min_version]
#
# 'RequiredAppsInDomain' in the ini only makes the App Center check that Kelvin
# is installed somewhere in the domain, not which version. This reads the
# installed versions from the same LDAP objects the App Center checks for
# RequiredAppsInDomain (resolve_dependencies() in appcenter utils.py): an
# appcenter/app object for ucsschool-kelvin-rest-api installed on at least one
# server. univentionAppID is stored as "<id>_<version>"; the installed version
# is exposed separately as univentionAppVersion.
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
#   0 - a Kelvin >= the minimum, or a branch test version, is installed in the
#       domain
#   1 - Kelvin is not installed anywhere in the domain
#   2 - Kelvin is installed, but every version is too old
check_kelvin_version() {
    local min_version="${1:-$MIN_KELVIN_VERSION}"

    local versions
    versions="$(univention-ldapsearch -LLL \
        "(&(univentionObjectType=appcenter/app)(univentionAppInstalledOnServer=*)(univentionAppID=ucsschool-kelvin-rest-api_*))" \
        univentionAppVersion \
        2>/dev/null | sed -n 's/^univentionAppVersion: //p')"

    if [[ -z "$versions" ]]; then
        return 1
    fi

    # Feed the versions on stdin (one per line) so values containing spaces
    # (e.g. "5.2 v3", which LooseVersion supports) survive intact.
    if printf '%s\n' "$versions" | python3 -c '
import sys

from univention.appcenter.app import LooseVersion

required = LooseVersion(sys.argv[1])
versions = [line.strip() for line in sys.stdin if line.strip()]
sys.exit(
    0
    if any(
        version.startswith("0.0.0-") or LooseVersion(version) >= required
        for version in versions
    )
    else 1
)
' "$min_version"; then
        return 0
    fi

    return 2
}
