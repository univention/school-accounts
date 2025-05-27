<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {computed, onMounted, reactive, ref, type ComputedRef, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {useTranslation} from 'i18next-vue';
import {
  useStandby,
  UButton,
  UMultiSelect,
  UComboBox,
  UGrid,
  UStandbyFullScreen,
  type UGridContextAction,
  type UGridRow,
  UConfirmDialog,
} from '@univention/univention-veb';
import {getListViewConfig, getUsers, deleteUsers, getDataAdapter} from '@/helpers/dataAccess';
import type {GridRow, ListViewConfig, ListViewState} from '@/helpers/models/interface';
import {useErrorStore} from '@/stores/error';
import SiteHeader from '@/components/SiteHeader.vue';

const {t} = useTranslation();

/** Stores **/

const errorStore = useErrorStore();
const router = useRouter();
const route = useRoute();

/** Refs **/

const loading = ref(true);
const standby = reactive(useStandby());

const config = ref<ListViewConfig>({
  schools: [],
  groups: {
    schoolClasses: {
      columns: [],
      rows: [],
    },
    workGroups: {
      columns: [],
      rows: [],
    },
  },
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

const globalActions = computed(() => {
  const canAdd = (): boolean => {
    const currentSchool = state.value.users.searchFormValues.school;
    const schoolConfig = config.value.schools.filter(school => school.value === currentSchool)[0];
    if (schoolConfig) {
      return schoolConfig.permissions.includes('add');
    }
    return false;
  };

  return [
    {
      label: t('ListView.globalActions.addLabel'),
      icon: 'plus',
      callback: onAdd,
      disabled: !canAdd(),
    },
  ];
});

const editContextAction: ComputedRef<UGridContextAction> = computed(() => ({
  label: t('ListView.contextActions.editLabel'),
  icon: 'edit-2',
  callback: onEdit,
  canExecute: (row: UGridRow) => typeof row !== 'undefined',
  multi: false,
}));

const contextActions: ComputedRef<UGridContextAction[]> = computed(() => {
  const canDo =
    (action: string): ((row: UGridRow) => boolean) =>
    (row: UGridRow) =>
      (row as GridRow).allowedActions.includes(action);

  const actions: UGridContextAction[] = [
    editContextAction.value,
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

const searchDisabled = computed(() => {
  const searchFormValues = Object.entries(state.value.users.searchFormValues);
  const atLeastOneSelection =
    searchFormValues.filter(entry => {
      const selection = entry[1];
      return selection !== undefined && selection !== '';
    }).length > 0;
  return !atLeastOneSelection;
});

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
  state.value.users.searchFormValues.schoolClasses = result.value.groups.schoolClasses.rows.map(row => row.id);
  state.value.users.searchFormValues.workGroups = result.value.groups.workGroups.rows.map(row => row.id);
};

const onAdd = (): void => {
  const currentSchool = state.value.users.searchFormValues.school;
  router.push({
    name: 'add',
    query: {school: encodeURIComponent(currentSchool)},
  });
};

const onEdit = (ids: string[]): void => {
  const currentSchool = state.value.users.searchFormValues.school;
  router.push({
    name: 'edit',
    params: {id: encodeURIComponent(ids[0])},
    query: {school: encodeURIComponent(currentSchool)},
  });
};

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

const onSearch = async (keepSelection = false) => {
  const school = state.value.users.searchFormValues.school;
  const schoolClasses = state.value.users.searchFormValues.schoolClasses;
  const workGroups = state.value.users.searchFormValues.workGroups;
  if (school === '' || school === undefined) {
    return;
  }

  await standby.wrap(async () => {
    const result = await getUsers(school, schoolClasses, workGroups);
    if (!result.ok) {
      errorStore.push({
        message: t('ListView.fetchObjects.error', {msg: result.error}),
        unRecoverable: false,
      });
      return;
    }
    state.value.users.rows = result.value.users;

    if (keepSelection) {
      const rowIds = new Set(state.value.users.rows.map(row => row.id));
      state.value.users.rowSelection = state.value.users.rowSelection.filter(selectionId => rowIds.has(selectionId));
    } else {
      state.value.users.rowSelection = [];
    }
  });
};

/** Watches **/

watch(
  () => state.value.users.searchFormValues.school,
  async school => {
    // update config on school change
    const dataAdapter = await getDataAdapter();

    const [schoolClassesConfigResult, workGroupConfigResult] = await Promise.all([
      dataAdapter.fetchSchoolClassConfig(school),
      dataAdapter.fetchWorkGroupConfig(school),
    ]);

    if (!schoolClassesConfigResult.ok) {
      return schoolClassesConfigResult;
    }
    if (!workGroupConfigResult.ok) {
      return workGroupConfigResult;
    }
    config.value.groups.schoolClasses.rows = schoolClassesConfigResult.value.rows;
    config.value.groups.workGroups.rows = workGroupConfigResult.value.rows;
  }
);

watch(
  () => route.query['refetch'],
  async val => {
    if (val !== undefined) {
      const query = JSON.parse(JSON.stringify(route.query));
      delete query.refetch;
      router.replace({
        ...route,
        query,
      });
      if (state.value.users.rows.length > 0) {
        await onSearch(true);
      }
    }
  },
  {
    immediate: true,
  }
);

onMounted(async () => {
  await standby.wrap(() => loadConfig());
  loading.value = false;
});
</script>

<template>
  <SiteHeader />
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
      @submit.prevent="onSearch()"
    >
      <div class="searchForm__elements">
        <div>
          <UComboBox
            name="school"
            :label="$t('ListView.searchForm.school.label')"
            :description="$t('ListView.searchForm.school.description')"
            :required="true"
            :options="config.schools"
            v-model:modelValue="state.users.searchFormValues.school"
          />
        </div>
        <div>
          <UMultiSelect
            name="school_classes"
            class="group_selection"
            :label="$t('ListView.searchForm.school_classes.label')"
            :description="$t('ListView.searchForm.school_classes.description')"
            :required="false"
            :columns="config.groups.schoolClasses.columns"
            :rows="config.groups.schoolClasses.rows"
            v-model:modelValue="state.users.searchFormValues.schoolClasses"
          />
        </div>
        <div>
          <UMultiSelect
            name="work_groups"
            class="group_selection"
            :label="$t('ListView.searchForm.workGroups.label')"
            :description="$t('ListView.searchForm.workGroups.description')"
            :required="false"
            :columns="config.groups.workGroups.columns"
            :rows="config.groups.workGroups.rows"
            v-model:modelValue="state.users.searchFormValues.workGroups"
          />
        </div>
      </div>
      <div class="searchForm__buttons">
        <UButton
          primary
          :disabled="searchDisabled"
          type="submit"
          icon=""
          :label="$t('ListView.searchForm.searchButton.label')"
        />
      </div>
    </form>

    <UGrid
      class="listView__uGrid"
      v-model:selection="state.users.rowSelection"
      :columns="config.users.columns"
      :globalActions="globalActions"
      :rows="state.users.rows"
      :contextActions="contextActions"
      :itemsPerPageOptions="[20, 50, -1]"
      :clickCallback="editContextAction"
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
  <UStandbyFullScreen :active="!!standby.active" />
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
  .group_selection
    .uTable
      max-height: 6rem

#header ~ .listView
  padding-top: calc(var(--layout-height-header) + (2 * var(--layout-spacing-unit)))
</style>
