// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {UGridRow} from '@univention/univention-veb';

// NOTE: This is currently only used for generating mock data.
export interface SchoolClass extends UGridRow {
  school: string;
}
