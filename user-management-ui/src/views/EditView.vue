<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {computed, onMounted, onUnmounted, ref} from 'vue';
import {useRouter, type RouteLocationRaw} from 'vue-router';
import {useTranslation} from 'i18next-vue';
import {UButton} from '@univention/univention-veb';

const {t} = useTranslation();

/** Stores **/

const router = useRouter();

/** Refs **/

const windowScroll = ref(0);

const heading = computed(() => {
  return `${t('EditView.heading.add')}`;
});

/** Helper functions **/

const onBack = (refetchGrid = false): void => {
  const route: RouteLocationRaw = {
    name: 'users',
  };
  if (refetchGrid) {
    route.query = {
      refetch: 'true',
    };
  }
  router.push(route);
};

const onScroll = (): void => {
  windowScroll.value = window.scrollY;
};

onMounted(() => {
  window.addEventListener('scroll', onScroll, {passive: true});
  onScroll();
});

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll);
});
</script>

<template>
  <div>
    <main class="editView">
      <div
        class="editView__stickyHeader"
        :class="{'editView__stickyHeader--bordered': windowScroll > 0}"
      >
        <div class="listView__header">
          <h1 class="listView__header__heading">
            {{ heading }}
          </h1>
          <div class="listView__header__buttons">
            <UButton
              :label="$t('EditView.button.back')"
              @click="onBack(false)"
            />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style lang="stylus">
.editView
  .editView__stickyHeader
    position: sticky
    top: 0
    background: var(--bgc-content-body)
    z-index: var(--z-index-sticky)
    --local-border-color: transparent
    border-bottom: 1px solid var(--local-border-color)
    transition: border-color 200ms
    &--bordered
      --local-border-color: var(--font-color-contrast-low)

.editView .listView__header
  padding: calc(4 * var(--layout-spacing-unit))
  margin: 0 auto
  max-width: 1140px
  display: flex
  align-items: flex-start
  flex-wrap: wrap
  gap: var(--layout-spacing-unit) 0
  min-height: var(--button-size)

.editView .listView__header__buttons
  margin-left: auto
  display: flex
  flex-wrap: wrap
  justify-content: flex-end
  grid-gap: calc(2 * var(--layout-spacing-unit))

.uFormElement--hidden
  display: none !important
</style>
