#!/bin/bash
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

echo $(echo $LDAP_HOSTDN | cut -d= -f2 | cut -d, -f1)\$ > /etc/machine.user
chmod 600 /etc/machine.user