<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {computed, onMounted, reactive, ref} from 'vue';
import {useTranslation} from 'i18next-vue';
import {useStandby, UButton, UComboBox, UGrid, UStandbyFullScreen} from '@univention/univention-veb';
import {getListViewConfig, getUsers} from '@/helpers/dataAccess';
import {type ListViewConfig, type ListViewState} from '@/helpers/models/interface';
import {useErrorStore} from '@/stores/error';

const {t} = useTranslation();

/** Stores **/

const errorStore = useErrorStore();

/** Refs **/

const loading = ref(true);
const standby = reactive(useStandby());

const config = ref<ListViewConfig>({
  schools: [],
  users: {
    columns: [],
  },
});

const state = ref<ListViewState>({
  users: {
    searchFormValues: {},
    rowSelection: [],
    rows: [],
  },
});

const searchDisabled = computed(() => {
  const searchFormValues = Object.entries(state.value.users.searchFormValues);
  const atLeastOneSelection =
    searchFormValues.filter(entry => {
      const selection = entry[1];
      return selection !== undefined && selection !== '';
    }).length > 0;
  return !atLeastOneSelection;
});

/** Helper functions **/

const loadConfig = async () => {
  const result = await getListViewConfig();
  if (!result.ok) {
    errorStore.push({
      message: t('ListView.fetchConfig.error', {msg: result.error}),
      unRecoverable: true,
    });
    return;
  }
  config.value = result.value;
  state.value.users.searchFormValues.school = result.value.schools[0]?.value || '';
};

const search = async () => {
  const school = state.value.users.searchFormValues.school;
  if (school === '' || school === undefined) {
    return;
  }

  await standby.wrap(async () => {
    const result = await getUsers(school);
    if (!result.ok) {
      errorStore.push({
        message: t('ListView.fetchObjects.error', {msg: result.error}),
        unRecoverable: false,
      });
      return;
    }
    state.value.users.rows = result.value.users;
  });
};

onMounted(async () => {
  await standby.wrap(() => loadConfig());
  loading.value = false;
});
</script>

<template>
  <main
    v-if="!loading"
    class="listView"
  >
    <div class="listView__header">
      <h1 class="listView__header__heading">
        {{ $t('ListView.header') }}
      </h1>
      <h2 class="listView__header__subheading">
        {{ $t('ListView.subheader') }}
      </h2>
    </div>

    <form
      class="searchForm"
      @submit.prevent="search()"
    >
      <div class="searchForm__elements">
        <UComboBox
          name="school"
          :label="$t('ListView.searchForm.school.label')"
          :description="$t('ListView.searchForm.school.description')"
          :required="true"
          :options="config.schools"
          v-model:modelValue="state.users.searchFormValues.school"
        />
      </div>
      <div class="searchForm__buttons">
        <UButton
          primary
          :disabled="searchDisabled"
          type="submit"
          icon="search"
          :label="$t('ListView.searchForm.searchButton.label')"
        />
      </div>
    </form>

    <UGrid
      class="listView__uGrid"
      v-model:selection="state.users.rowSelection"
      :columns="config.users.columns"
      :rows="state.users.rows"
      :itemsPerPageOptions="[20, 50, -1]"
    />
  </main>
  <UStandbyFullScreen :active="standby.active" />
</template>

<style lang="stylus">
main.listView
  padding: calc(4 * var(--layout-spacing-unit))
  margin: 0 auto
  height: 100vh
  display: flex
  flex-direction: column
  max-width: 1140px

  h1
    margin: 0
    margin-bottom: calc(2 * var(--layout-spacing-unit))

  h2
    margin: 0
    margin-bottom: calc(2 * var(--layout-spacing-unit))

  .searchForm__elements
    display: flex
    gap: var(--layout-spacing-unit) calc(2 * var(--layout-spacing-unit))

    .uFormElement
      flex: 1 1 auto

  .searchForm__buttons
    display: flex
    justify-content: flex-end
    grid-gap: calc(2 * var(--layout-spacing-unit))

  .listView__uGrid
    margin-top: calc(4 * var(--layout-spacing-unit))
</style>
