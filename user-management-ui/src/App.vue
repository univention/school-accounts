<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import DefaultRouterView from '@/components/DefaultRouterView.vue';
import {onMounted, ref} from 'vue';
import {useSettingsStore} from '@/stores/settings';
import {useRouter} from 'vue-router';
import {useAdapterStore} from '@/stores/adapter';
import {useTranslation} from 'i18next-vue';
import {useErrorStore} from '@/stores/error';

const router = useRouter();
const loading = ref(true);
const {t} = useTranslation();
const errors = useErrorStore();

onMounted(async () => {
  try {
    const settingsStore = useSettingsStore();
    await settingsStore.init();

    const adapterStore = useAdapterStore(settingsStore.config);
    // We need to wait until the routes are loaded;
    // otherwise, login will always redirect back to '/',
    // instead of the requested route.
    await router.isReady();
    const isAuthenticated = await adapterStore.authenticationAdapter.authenticate();
    if (!isAuthenticated) {
      errors.push({
        message: t('App.error.loginFailed'),
        unRecoverable: true,
      });
    }
  } catch (error) {
    console.error(error);
    errors.push({
      message: t('App.error.config'),
      unRecoverable: true,
    });
    loading.value = false;
    return;
  }

  loading.value = false;
});
</script>

<template>
  <DefaultRouterView
    :keepAlive="{include: 'ListView'}"
    :loading="loading"
  />
</template>
