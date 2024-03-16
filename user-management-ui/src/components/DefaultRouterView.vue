<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<!--
The intent of this component is to refactor common code into something we
could put into univention-veb.

Please do not put anything in here that is app-specific.
-->

<script setup lang="ts">
import {type KeepAliveProps} from 'vue';
import {UConfirmDialog, UStandbyFullScreen} from '@univention/univention-veb';
import {useErrorStore} from '@/stores/error';

const errors = useErrorStore();

interface Props {
  keepAlive?: KeepAliveProps;
  loading: boolean;
}
defineProps<Props>();
</script>

<template>
  <UStandbyFullScreen :active="loading" />
  <template v-if="!loading">
    <div
      v-if="errors.activeError && errors.activeError.unRecoverable"
      class="app__errorMessage"
    >
      <div class="uCard uContainer">
        <h1>
          {{ errors.activeError.title || $t('ErrorModal.heading') }}
        </h1>
        {{ errors.activeError.message }}
      </div>
    </div>
    <RouterView
      v-else
      v-slot="{Component}"
    >
      <KeepAlive v-bind="keepAlive">
        <component :is="Component" />
      </KeepAlive>
      <UConfirmDialog
        :active="!!errors.activeError"
        :title="errors.activeError?.title || $t('ErrorModal.heading')"
        :confirmLabel="$t('ErrorModal.button.confirmation')"
        hideCancel
        @confirm="errors.advance"
      >
        <template #description>
          <p>{{ errors.activeError?.message }}</p>
        </template>
      </UConfirmDialog>
    </RouterView>
  </template>
</template>

<style lang="stylus">
.app__errorMessage
  position: fixed
  inset: 0
  display: flex
  align-items: center
  justify-content: center
  padding: calc(2 * var(--layout-spacing-unit))
</style>
