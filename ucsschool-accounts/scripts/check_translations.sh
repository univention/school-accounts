#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Script to update translations. Fails if untranslated strings are found.
set -e

SCRIPTS_PATH="$(cd "$(dirname "$0")" && pwd)"
PROJECT_PATH="$(cd "$SCRIPTS_PATH/.." && pwd)"
TRANSLATIONS_PATH="$PROJECT_PATH/locales/de/LC_MESSAGES"
APP_ID="ucsschool-accounts"
POT="$TRANSLATIONS_PATH/$APP_ID.pot"
PO="$TRANSLATIONS_PATH/$APP_ID.po"

trap 'rm -f "$POT"' EXIT

echo "Verifying translations..."

# pybabel extracts, gettext merges and compiles. pybabel is the only extractor
# that reads Jinja, so one mapping covers `*.py` and the `{{ _("...") }}` literals
# in `templates/`. `pybabel update` is deliberately not used for the merge: it
# rewrites the PO header on every run, leaving the catalog dirty and failing this
# check spuriously.
#
# --msgid-bugs-address: msgmerge copies the field from the template, so leaving it
# unset writes Babel's "EMAIL@ADDRESS" placeholder into the catalog.
uv run --project "$PROJECT_PATH" --frozen pybabel --quiet extract \
    --mapping-file "$PROJECT_PATH/babel.cfg" \
    --msgid-bugs-address "ucsschool-maintainers@univention.de" \
    --no-location \
    --sort-output \
    -o "$POT" \
    "$PROJECT_PATH/ucsschool_accounts"
msgmerge --quiet -F --update --backup off "$PO" "$POT"

# `^msgid "[^"]` skips the PO header, whose msgid is the empty string.
# --no-wrap: msgattrib re-wraps long entries, emitting a bare `msgid ""` whose text
# sits on continuation lines the anchored grep cannot see.
if msgattrib --no-wrap --only-fuzzy --no-obsolete "$PO" | grep -q '^msgid "[^"]'; then
    echo "Fuzzy strings! Review them in $PO and run this script again"
    exit 1
fi
if msgattrib --no-wrap --untranslated --no-obsolete "$PO" | grep -q '^msgid "[^"]'; then
    echo "Untranslated strings! Translate them in $PO and run this script again"
    exit 1
fi

echo "Compiling translations..."
"$SCRIPTS_PATH/translate.sh"

echo "Success!"
