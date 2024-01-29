#!/bin/bash

# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

poetry -C $PROJECT_DIR/user-management-bff install
yarn --cwd $PROJECT_DIR/user-management-ui install