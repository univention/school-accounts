# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

package guardian.conditions

import future.keywords.if

condition("ucsschool-user-management:conditions:action_is_creation", parameters, condition_data) if {
	is_null(condition_data.target.old)
} else if {
	condition_data.target.old == {}
} else = false
