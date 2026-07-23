#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from os import environ
import xml.etree.ElementTree as ET  # nosec


def main():
    junit_result_filename = environ["PLAYWRIGHT_JUNIT_OUTPUT_NAME"]
    base_url = environ.get("PLAYWRIGHT_TEST_BASE_URL", None)
    tree = ET.parse(junit_result_filename)  # nosec
    root = tree.getroot()
    suite_prefix = ""
    if base_url:
        suite_prefix = f"{base_url}."
    for testsuite in root:
        if testsuite.tag != "testsuite":
            continue
        for testcase in testsuite:
            if testcase.tag != "testcase":
                continue
            testcase.attrib["classname"] = (
                f'{suite_prefix}{testsuite.attrib["hostname"]}.{testcase.attrib["classname"]}'
            )
    tree.write(junit_result_filename)


if __name__ == "__main__":
    main()
