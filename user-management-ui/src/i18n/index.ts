// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import i18next from 'i18next';
import {getCookie} from '@univention/univention-veb';

import de from '@/i18n/locales/de.json';
import en from '@/i18n/locales/en.json';

interface AvailableLanguage {
  id: string;
  label: string;
}
export let availableLanguages: AvailableLanguage[] = [
  {
    id: 'de-DE',
    label: 'Deutsch',
  },
  {
    id: 'en-US',
    label: 'English',
  },
];

const getMatchingAvailableLng = (lng: string): AvailableLanguage | null => {
  const lngLowerCase = lng.toLowerCase();
  const exactMatch = availableLanguages.find(availableLanguage => availableLanguage.id.toLowerCase() === lngLowerCase);
  if (exactMatch) {
    return exactMatch;
  }
  const shortLng = lngLowerCase.slice(0, 2);
  const shortMatch = availableLanguages.find(
    availableLanguage => availableLanguage.id.slice(0, 2).toLowerCase() === shortLng
  );
  if (shortMatch) {
    return shortMatch;
  }
  return null;
};
const validateLanguagesJSON = (data: unknown) => {
  return (
    Array.isArray(data) &&
    data.every(
      entry => Object.prototype.hasOwnProperty.call(entry, 'id') && Object.prototype.hasOwnProperty.call(entry, 'label')
    )
  );
};

export const setLanguage = (lng: string): void => {
  const date = new Date();
  date.setTime(date.getTime() + 100 * 24 * 60 * 60 * 1000); // 100 days
  document.cookie = `UMCLang=${lng}; expires=${date.toUTCString()}; path=/univention/;`;
};

export const initializeI18next = async () => {
  if (import.meta.env.PROD) {
    try {
      const response = await fetch('/univention/languages.json');
      if (response.ok) {
        const _availableLanguages: AvailableLanguage[] = await response.json();
        if (validateLanguagesJSON(_availableLanguages)) {
          const _availableLanguagesIds = new Set(_availableLanguages.map(o => o.id));

          availableLanguages = availableLanguages.reduce((acc, language) => {
            if (language.id === 'en-US' || _availableLanguagesIds.has(language.id)) {
              acc.push(language);
            }
            return acc;
          }, [] as AvailableLanguage[]);
        } else {
          console.error('languages.json has wrong format');
        }
      }
    } catch (e) {
      console.error('Failed to load/parse /univention/languages.json : ', e);
    }
  }

  let match = null;
  const preferredLng = getCookie('UMCLang');
  if (preferredLng) {
    match = getMatchingAvailableLng(preferredLng);
  }
  if (!match) {
    window.navigator.languages.some(navigatorLng => {
      match = getMatchingAvailableLng(navigatorLng);
      return !!match;
    });
  }
  const lng = match?.id || 'en-US';

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
    lng,
    fallbackLng: 'en',
    resources: {
      de: {userManagementUi: de},
      en: {userManagementUi: en},
    },
  });
};
