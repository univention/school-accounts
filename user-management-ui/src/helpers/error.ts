// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';

export const errorToString = (err: unknown): string => {
  let errorMessage = i18next.t('errors.unknownError');
  if (err instanceof Error) {
    errorMessage = err.toString();
  } else if (typeof err === 'string') {
    errorMessage = err;
  } else {
    try {
      errorMessage = JSON.stringify(err);
    } catch (err) {
      // ignore
    }
  }
  return errorMessage;
};
