// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import '@univention/univention-veb/style.css';

import {createApp} from 'vue';
import {createPinia} from 'pinia';
import i18next from 'i18next';
import I18NextVue from 'i18next-vue';
import {UniventionVebPlugin} from '@univention/univention-veb';

import {initializeI18next} from '@/i18n';
import App from '@/App.vue';
import router from '@/router';

const pinia = createPinia();

initializeI18next().then(() => {
  document.documentElement.setAttribute('lang', i18next.language.slice(0, 2));
  // @ts-ignore --  This works, but `use` isn't happy with the `UniventionVebPlugin`
  const app = createApp(App).use(router).use(I18NextVue, {i18next}).use(UniventionVebPlugin, {i18next}).use(pinia);

  app.mount('#app');
});
