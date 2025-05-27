# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

package guardian.conditions

import future.keywords.every
import future.keywords.if
import future.keywords.in

import data.univention.utils.extract_role_and_context

condition("ucsschool-user-management:conditions:actor_is_in_group", parameters, condition_data) if {
	target_role_and_context := extract_role_and_context(condition_data.target.old.roles[_])
	split(target_role_and_context.role, ":")[2] == "workgroup"
	school := condition_data.target.old.attributes.school
	condition_data.actor.attributes.work_groups[school][_] == condition_data.target.old.attributes.id
} else if {
	target_role_and_context := extract_role_and_context(condition_data.target.old.roles[_])
	split(target_role_and_context.role, ":")[2] == "school_class"
	school := condition_data.target.old.attributes.school
	condition_data.actor.attributes.school_classes[school][_] == condition_data.target.old.attributes.id
} else := false
