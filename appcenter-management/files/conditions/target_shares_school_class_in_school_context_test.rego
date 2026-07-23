# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

package univention.target_shares_school_class_in_school_context_test

import data.guardian.conditions.condition
import future.keywords.every
import future.keywords.if

target_shares_school_class_in_school_context_parametrize := [
	{
		"condition_data": {
			"actor": {"attributes": {"school_classes": {"school1": ["1a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {},
				"new": {"attributes": {"school_classes": {"school1": ["1a"]}}},
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
			"actor": {"attributes": {"school_classes": {"school1": ["2a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {},
				"new": {"attributes": {"school_classes": {"school1": ["1a"]}}},
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
			"actor": {"attributes": {"school_classes": {"school1": ["1a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {},
				"new": {"attributes": {"school_classes": {"school2": ["1a"]}}},
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
			"actor": {"attributes": {"school_classes": {"school1": ["1a", "2a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {},
				"new": {"attributes": {"school_classes": {"school1": ["3b", "2a"]}}},
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
			"actor": {"attributes": {"school_classes": {"school2": ["1a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {},
				"new": {"attributes": {"school_classes": {"school2": ["1a"]}}},
			},
			"namespaces": {},
			"contexts": set(),
			"extra_args": {},
		},
		"parameters": {},
		"result": false,
	},
]

test_target_shares_school_class_in_school_context if {
	every case in target_shares_school_class_in_school_context_parametrize {
		result := condition("ucsschool-user-management:conditions:target_shares_school_class_in_school_context", case.parameters, case.condition_data)

		# regal: ignore:print-or-trace-call
		print("TEST_DEBUG result: ", result, " expected: ", case.result)
		result == case.result
	}
}
