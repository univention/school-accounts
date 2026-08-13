#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Fail the CI job if any test in the collected junit reports failed.

The test commands in ``integration_tests.cfg`` end in ``|| true`` so that a
failing test run does not abort the cfg run before the junit reports have been
fetched from the VM.  This script restores the failure afterwards.
"""

import pathlib
import sys
import xml.etree.ElementTree as ET  # nosec

JUNIT_GLOB = "*junit.xml"


def count_errors(junit_file: pathlib.Path) -> int:
    tree = ET.parse(junit_file)  # noqa: S314
    root = tree.getroot()
    testsuites = root.findall("testsuite") if root.tag == "testsuites" else [root]
    return sum(
        int(testsuite.attrib.get("errors", "0"))
        + int(testsuite.attrib.get("failures", "0"))
        for testsuite in testsuites
    )


def main() -> int:
    junit_files = sorted(pathlib.Path().glob(JUNIT_GLOB))
    if not junit_files:
        print(f"No junit report matching {JUNIT_GLOB!r} was collected.")
        return 1

    error_counter = 0
    for junit_file in junit_files:
        errors = count_errors(junit_file)
        print(f"Parsing {junit_file}: {errors} errors.")
        error_counter += errors

    if error_counter > 0:
        print(f"Found {error_counter} errors.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
