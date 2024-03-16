// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type Attribute} from '@univention/univention-veb';

export type ContextAction = 'delete';
export interface UserResponseData {
  id: string;
  attributes: Record<string, Attribute>;
  allowedActions: ContextAction[];
}

export interface UsersResponse {
  users: UserResponseData[];
}

export interface User {
  id: string;
  attributes: Record<string, Attribute>;
  allowedActions: ContextAction[];
}

export interface WrappedUsersList {
  users: User[];
}
