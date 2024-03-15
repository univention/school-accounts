// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type Attribute} from '@univention/univention-veb';

export type ContextAction = 'delete';

export type UserData = Record<string, any>;

export interface UserResponseData {
  id: string;
  attributes: Record<string, Attribute>;
  allowedActions: ContextAction[];
}

export interface UserResponse {
  user: UserResponseData;
}

export interface UsersResponse {
  users: UserResponseData[];
}

export interface User {
  id: string;
  attributes: Record<string, Attribute>;
  allowedActions: ContextAction[];
}

export interface WrappedUser {
  user: User;
}

export interface WrappedUsersList {
  users: User[];
}
