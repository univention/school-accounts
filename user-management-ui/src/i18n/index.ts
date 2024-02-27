// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';

import de from '@/i18n/locales/de.json';
import en from '@/i18n/locales/en.json';

const availableLanguages = ['en', 'de'];

export const initializeI18next = async () => {
  return i18next.init({
    interpolation: {
      // WARNING: We are setting this to false,
      // because Vue templates/render functions already escape the content,
      // and we don't need a double escape.
      // Set this to true if you use i18next translation with interpolations
      // inside v-html or manually insert them into the DOM.
      escapeValue: false,
      // WARNING: We are setting this to false,
      // because all variables should be provided internally for rendering.
      // If we use user-supplied elements that are translated,
      // set this to true.
      skipOnVariables: false,
    },
    ns: ['userManagementUi'],
    lng: 'en',
    fallbackLng: availableLanguages,
    resources: {
      de: {userManagementUi: de},
      en: {userManagementUi: en},
    },
  });
};
