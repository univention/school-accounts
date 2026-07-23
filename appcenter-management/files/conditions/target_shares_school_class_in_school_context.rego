# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

package guardian.conditions

import future.keywords.every
import future.keywords.if
import future.keywords.in

import data.univention.utils.extract_role_and_context

condition("ucsschool-user-management:conditions:target_shares_school_class_in_school_context", parameters, condition_data) if {
	actor_context := condition_data.actor_role.context
	context_split = split(actor_context, ":")
	school := context_split[2]
	condition_data.actor.attributes.school_classes[school][_] == condition_data.target.new.attributes.school_classes[school][_]
} else = false
