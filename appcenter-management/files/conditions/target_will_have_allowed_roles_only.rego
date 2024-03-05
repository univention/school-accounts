# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

package guardian.conditions

import future.keywords.every
import future.keywords.if
import future.keywords.in

import data.univention.utils.extract_role_and_context

condition("ucsschool-user-management:conditions:target_will_have_allowed_roles_only", parameters, condition_data) if {
	allowed_roles = split(parameters.roles, ",")
	every target_crole in condition_data.target.new.roles {
		target_role_and_context := extract_role_and_context(target_crole)
		target_role_and_context.role in allowed_roles
	}
} else = false
