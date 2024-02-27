// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {createRouter, createWebHistory} from 'vue-router';
import ListView from '@/views/ListView.vue';
import PageNotFound from '@/views/PageNotFound.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'users',
      component: ListView,
    },
    {
      path: '/:pathMatch(.*)*',
      component: PageNotFound,
    },
  ],
});

export default router;
