# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Puts multiline translation strings onto a single line,
# for the purposes of identifying untranslated strings
:start
N
s/"\n"/ /
bstart
