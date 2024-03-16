<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {computed, onMounted, reactive, ref, type ComputedRef} from 'vue';
import {useTranslation} from 'i18next-vue';
import {
  useStandby,
  UButton,
  UComboBox,
  UGrid,
  UStandbyFullScreen,
  type UGridContextAction,
  type UGridRow,
  UConfirmDialog,
} from '@univention/univention-veb';
import {getListViewConfig, getUsers, deleteUsers} from '@/helpers/dataAccess';
import type {ListViewConfig, ListViewState, GridRow} from '@/helpers/models/interface';
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

const onDelete = async (ids: string[]): Promise<void> => {
  deleteModalActive.value = false;
  const failedUsers = await standby.wrap(() => deleteUsers(ids));
  if (failedUsers.length) {
    deleteModalError.failedUsers = failedUsers;
    deleteModalError.active = true;
  }

  // remove successfully deleted objects from list and selection
  const failedIdsSet = new Set(failedUsers.map(x => x.id));
  const successes = new Set(ids.filter(id => !failedIdsSet.has(id)));
  state.value.users.rows = state.value.users.rows.filter(row => !successes.has(row.id));
  state.value.users.rowSelection = state.value.users.rowSelection.filter(id => !successes.has(id));
};
const deleteModalError = reactive({
  active: false,
  failedUsers: [] as {id: string; error: string}[],
});
const deleteModalActive = ref(false);
const deleteModalProps = reactive<{
  selected: string[];
  toDelete: string[];
}>({
  selected: [],
  toDelete: [],
});

const canDo =
  (action: string): ((row: UGridRow) => boolean) =>
  (row: UGridRow) =>
    (row as GridRow).allowedActions.includes(action);
const contextActions: ComputedRef<UGridContextAction[]> = computed(() => {
  const actions: UGridContextAction[] = [
    {
      label: t('ListView.contextActions.deleteLabel'),
      icon: 'trash',
      callback: (ids: string[], objectsToDelete: UGridRow[], sel: string[]): void => {
        deleteModalProps.selected = sel;
        deleteModalProps.toDelete = ids;
        deleteModalActive.value = true;
      },
      canExecute: canDo('delete'),
      multi: true,
      enablingMode: 'some',
    },
  ];
  return actions;
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
      :contextActions="contextActions"
      :itemsPerPageOptions="[20, 50, -1]"
    />
    <UConfirmDialog
      v-model:active="deleteModalActive"
      :title="t('DeleteModal.title')"
      :confirmLabel="t('DeleteModal.confirmLabel')"
      :cancelLabel="t('DeleteModal.cancelLabel')"
      @confirm="onDelete(deleteModalProps.toDelete)"
    >
      <template #description>
        <div>
          <p>
            {{
              t('DeleteModal.description', {
                toDelete: deleteModalProps.toDelete.length,
                selected: deleteModalProps.selected.length,
              })
            }}
          </p>
          <p v-if="deleteModalProps.toDelete.length !== deleteModalProps.selected.length">
            {{
              t('DeleteModal.warning', {
                numberWarning: deleteModalProps.selected.length - deleteModalProps.toDelete.length,
                selected: deleteModalProps.selected.length,
              })
            }}
          </p>
        </div>
      </template>
    </UConfirmDialog>
    <UConfirmDialog
      v-model:active="deleteModalError.active"
      :title="t('DeleteModalError.title')"
      :confirmLabel="t('DeleteModalError.confirmLabel')"
      hideCancel
    >
      <template #description>
        <div>
          <p>
            {{ t('DeleteModalError.description') }}
          </p>
          <ul>
            <li
              v-for="fail in deleteModalError.failedUsers"
              :key="fail.id"
            >
              {{ fail.id }} - {{ fail.error }}
            </li>
          </ul>
        </div>
      </template>
    </UConfirmDialog>
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
