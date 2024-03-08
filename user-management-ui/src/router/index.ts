// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {createRouter, createWebHistory} from 'vue-router';
import ListView from '@/views/ListView.vue';
import EditView from '@/views/EditView.vue';
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
      path: '/edit/:id/:page?',
      name: 'edit',
      component: EditView,
      props: {action: 'edit'},
    },
    {
      path: '/add/:page?',
      name: 'add',
      component: EditView,
      props: {action: 'add'},
    },
    {
      path: '/:pathMatch(.*)*',
      component: PageNotFound,
    },
  ],
});

export default router;
