<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {useRouter} from 'vue-router';
import {UButton} from '@univention/univention-veb';
import {useTranslation} from 'i18next-vue';
import SiteHeader from '@/components/SiteHeader.vue';

const {t} = useTranslation();
const router = useRouter();

const goHome = () => {
  router.push({name: 'users'});
};
</script>

<template>
  <SiteHeader />
  <main class="notFoundView">
    <h1>404: {{ t('NotFoundView.header') }}</h1>

    <p>{{ t('NotFoundView.body.text') }}</p>
    <UButton
      type="button"
      :label="t('NotFoundView.button.home')"
      @click="goHome"
    />
  </main>
</template>

<style lang="stylus">
main.notFoundView
  padding: calc(4 * var(--layout-spacing-unit))
  margin: 0 auto
  height: 100vh
  display: flex
  flex-direction: column
  max-width: 1140px
  text-align: center

  h1
    margin-top: 15%

  .uButton
    margin: calc(2 * var(--layout-spacing-unit)) auto
</style>
