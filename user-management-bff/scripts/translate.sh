#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Generate .mo binary translation files.

TRANSLATIONS_PATH="$(cd "$(dirname "$0")/.." && pwd)/locales/de/LC_MESSAGES"
APP_ID="ucsschool-user-management"

msgfmt -o "$TRANSLATIONS_PATH/$APP_ID.mo" "$TRANSLATIONS_PATH/$APP_ID.po"
