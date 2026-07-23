# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

package univention.target_will_have_allowed_roles_only_test

import data.guardian.conditions.condition
import future.keywords.every
import future.keywords.if

target_will_have_allowed_roles_only_parametrize := [
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {"roles": ["a:b:c"]},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {},
		"result": false,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {"roles": ["a:b:c"]},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {"roles": "a:b:c"},
		"result": true,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {"roles": ["a:b:c", "a:b:c&d:e:f"]},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {"roles": "a:b:c"},
		"result": true,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {"roles": ["a:b:c", "d:e:f"]},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {"roles": "a:b:c"},
		"result": false,
	},
	{
		"condition_data": {
			"actor": {},
			"actor_role": {},
			"target": {
				"old": {},
				"new": {"roles": ["a:b:c", "d:e:f"]},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {"roles": "a:b:c,d:e:f"},
		"result": true,
	},
]

test_target_will_have_allowed_roles_only if {
	every case in target_will_have_allowed_roles_only_parametrize {
		result := condition("ucsschool-user-management:conditions:target_will_have_allowed_roles_only", case.parameters, case.condition_data)

		# regal: ignore:print-or-trace-call
		print("TEST_DEBUG result: ", result, " expected: ", case.result)
		result == case.result
	}
}
