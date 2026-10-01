# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""The package version, taken from the release tag when the image is built.

hatchling calls :func:`get_version` while building the package. The image
build passes the tag in ``UCSSCHOOL_ACCOUNTS_BUILD_VERSION``; every other
build, a ``uv sync`` in the dev container or a CI test job, has no tag and
gets ``0.0.0``, so none of them needs a version input.

The module lives outside the package: it only runs at build time, and is
neither installed nor counted towards the coverage gate.
"""

from __future__ import annotations

import os
import re

_RELEASE_TAG = re.compile(r"(?:release-)?(?P<version>\d+\.\d+\.\d+)(?:-(?P<errata>errata\d+))?")


def get_version() -> str:
    """Turn ``release-1.0.0`` into ``1.0.0`` and ``release-1.0.0-errata1`` into ``1.0.0+errata1``.

    An errata release updates the image of an already published app version, so it
    keeps that version and names the errata in the PEP 440 local label.
    """
    match = _RELEASE_TAG.fullmatch(os.environ.get("UCSSCHOOL_ACCOUNTS_BUILD_VERSION", ""))
    if not match:
        return "0.0.0"
    if match["errata"]:
        return f"{match['version']}+{match['errata']}"
    return match["version"]
