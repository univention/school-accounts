// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

export type Result<T, E> =
  | {
      ok: true;
      value: T;
    }
  | {
      ok: false;
      error: E;
    };

export type SaveError =
  | {
      type: 'objectNotFound';
    }
  | {
      type: 'generic';
      message: string;
    }
  | {
      type: 'permissionsError';
      message: string;
      missingPermissions: string[];
    }
  | {
      type: 'fieldErrors';
      errors: {
        field: string;
        message: string;
      }[];
    };

export type FetchObjectError =
  | {
      type: 'objectNotFound';
    }
  | {
      type: 'generic';
      message: string;
    };

export type FieldError = {
  loc: string[];
  msg: string;
  type: string;
};
