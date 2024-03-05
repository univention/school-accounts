# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

package guardian.conditions

import future.keywords.every
import future.keywords.if
import future.keywords.in

import data.univention.utils.extract_role_and_context

condition("ucsschool-user-management:conditions:target_will_be_in_same_school_only", parameters, condition_data) if {
	actor_context := condition_data.actor_role.context
	every target_crole in condition_data.target.new.roles {
		target_role_and_context := extract_role_and_context(target_crole)
		actor_context == target_role_and_context.context
	}
} else = false
