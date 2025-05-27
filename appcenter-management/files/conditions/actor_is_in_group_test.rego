# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

package univention.actor_is_in_group_test

import data.guardian.conditions.condition
import future.keywords.every
import future.keywords.if

actor_is_in_group_parametrize := [
	{
		"condition_data": {
			"actor": {"attributes": {"school_classes": {"school1": ["1a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {"roles": ["a:b:school_class&a:b:school1"], "attributes": {"id": "1a", "school": "school1"}},
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
			"actor": {"attributes": {"work_groups": {"school1": ["wg"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {"roles": ["a:b:workgroup&a:b:school1"], "attributes": {"id": "wg", "school": "school1"}},
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
			"actor": {"attributes": {"school_classes": {"school1": ["1a"]}}},
			"actor_role": {"context": "a:b:school1"},
			"target": {
				"old": {"roles": ["a:b:workgroup&a:b:school1"], "attributes": {"id": "1a", "school": "school1"}},
				"new": {},
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
				"new": {},
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
				"old": {"roles": ["a:b:school_class&a:b:school1"], "attributes": {"id": "2a", "school": "school1"}},
				"new": {},
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
				"old": {"roles": ["a:b:school_class&a:b:school1"], "attributes": {"id": "1a", "school": "school2"}},
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

test_actor_is_in_group_test if {
	every case in actor_is_in_group_parametrize {
		result := condition("ucsschool-user-management:conditions:actor_is_in_group", case.parameters, case.condition_data)

		# regal: ignore:print-or-trace-call
		print("TEST_DEBUG result: ", result, " expected: ", case.result)
		result == case.result
	}
}
