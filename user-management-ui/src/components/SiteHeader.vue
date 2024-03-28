<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {UConfirmDialog, USelect} from '@univention/univention-veb';
import {availableLanguages, setLanguage} from '@/i18n';
import {reactive, ref} from 'vue';
import i18next from 'i18next';
import {useTranslation} from 'i18next-vue';

const {t} = useTranslation();

const props = withDefaults(
  defineProps<{
    confirmReload?: boolean;
  }>(),
  {
    confirmReload: false,
  }
);

const inIFrame = window.top !== window.self;
const showHeader = !inIFrame && availableLanguages.length > 1;
const languageOptions = availableLanguages.map(lng => ({label: lng.label, value: lng.id}));
const lng = ref(i18next.language);
const confirmModal = reactive<{
  active: boolean;
  previousLng: string;
}>({
  active: false,
  previousLng: '',
});
const setLngAndReload = (lng: string): void => {
  setLanguage(lng);
  window.location.reload();
};
const onCancel = (): void => {
  lng.value = confirmModal.previousLng;
};
const onUpdateModelValue = (value: string) => {
  if (props.confirmReload) {
    confirmModal.active = true;
    confirmModal.previousLng = lng.value;
  } else {
    setLngAndReload(value);
  }
  lng.value = value;
};
</script>

<template>
  <div
    v-if="showHeader"
    id="header"
  >
    <USelect
      :modelValue="lng"
      @update:modelValue="onUpdateModelValue"
      name="language"
      :options="languageOptions"
      :label="t('App.languageSelect')"
      icon="language"
      :hideLabelRow="true"
    />
  </div>
  <UConfirmDialog
    v-model:active="confirmModal.active"
    :title="t('Header.confirmReload.heading')"
    :confirmLabel="t('Header.confirmReload.button.confirm')"
    :cancelLabel="t('Header.confirmReload.button.cancel')"
    @cancel="onCancel"
    @confirm="setLngAndReload(lng)"
  >
    <template #description>
      <div>
        <p>
          {{ t('Header.confirmReload.text') }}
        </p>
      </div>
    </template>
  </UConfirmDialog>
</template>

<style lang="stylus">
#header
  background: var(--bgc-content-header)
  height: var(--layout-height-header)
  position: fixed
  z-index var(--z-index-sticky)
  top: 0
  left: 0
  right: 0
  display: flex
  align-items: center

  .uSelect
    width: fit-content
    margin: 0
    margin-right: calc(2 * var(--layout-spacing-unit))
    margin-left: auto
</style>
