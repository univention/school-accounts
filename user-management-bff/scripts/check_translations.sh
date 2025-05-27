#!/usr/bin/env sh
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Script to update translations. Fails if untranslated strings are found.
set -e

SCRIPTS_PATH="$(cd "$(dirname "$0")" && pwd)"
TRANSLATIONS_PATH="$(cd "$SCRIPTS_PATH/.." && pwd)/locales/de/LC_MESSAGES"
APP_ID="ucsschool-user-management"

echo "Verifying translations..."

# Note: Encountered problems when working with xgettext 0.24
# and f-strings -> Moved to old style `.format()` for that case
if [ ! -f "$TRANSLATIONS_PATH/$APP_ID.pot" ]; then
    find user-management-bff -name "*.py" | \
        xargs xgettext \
            --language Python \
            --from-code=UTF-8 \
            --keyword=_:1 \
            --keyword=translate \
            --no-location \
            -k \
            -o "$TRANSLATIONS_PATH/$APP_ID.pot"
    msgmerge -F --update --backup off "$TRANSLATIONS_PATH/$APP_ID.po" \
        "$TRANSLATIONS_PATH/$APP_ID.pot" > /dev/null
fi

rm "$TRANSLATIONS_PATH/$APP_ID.pot"

grep -q fuzzy $TRANSLATIONS_PATH/$APP_ID.po && \
    (echo "Fuzzy strings! Review them in $TRANSLATIONS_PATH/$APP_ID.po and run this script again"; exit 1)

sed -f "$SCRIPTS_PATH/check_translations.sed" "$TRANSLATIONS_PATH/$APP_ID.po" |
    grep -B 1 -A 1 '^msgstr ""' && \
    (echo "Untranslated strings! Translate them in $TRANSLATIONS_PATH/$APP_ID.po and run this script again"; exit 1)

echo "Compiling translations..."
$SCRIPTS_PATH/translate.sh

echo "Success!"
