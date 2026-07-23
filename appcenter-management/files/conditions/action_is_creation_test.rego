# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

package univention.action_is_creation_test

import data.guardian.conditions.condition
import future.keywords.every
import future.keywords.if

action_is_creation_parametrize := [
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {},
		"result": true,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": null,
				"new": {},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {},
		"result": true,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {"foo": "bar"},
				"new": {},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {},
		"result": false,
	},
]

test_action_is_creation if {
	every case in action_is_creation_parametrize {
		result := condition("ucsschool-user-management:conditions:action_is_creation", case.parameters, case.condition_data)

		# regal: ignore:print-or-trace-call
		print("TEST_DEBUG result: ", result, " expected: ", case.result)
		result == case.result
	}
}
