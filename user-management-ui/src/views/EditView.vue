<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import {
  defaultValue,
  type Field,
  type Page,
  UButton,
  UComboBox,
  UConfirmDialog,
  UExtendingInput,
  UIcon,
  UInputCheckbox,
  UInputClassified,
  UInputDate,
  UInputPassword,
  UInputText,
  UMultiInput,
  UMultiObjectSelect,
  UMultiSelect,
  USelect,
  useStandby,
  UStandbyFullScreen,
  UTransitionHeight,
} from '@univention/univention-veb';
import {computed, nextTick, onMounted, onUnmounted, reactive, ref, watch} from 'vue';
import {onBeforeRouteLeave, type RouteLocationRaw, RouterLink, useRoute, useRouter} from 'vue-router';
import {useTranslation} from 'i18next-vue';

import {createUser, fetchAddViewConfig, fetchEditViewConfig, updateUser} from '@/helpers/dataAccess';
import {useErrorStore} from '@/stores/error';
import type {EditViewConfig} from '@/helpers/models/config';
import type {FormValues} from '@/helpers/models/interface';
import type {SaveError} from '@/helpers/models/http';
import SiteHeader from '@/components/SiteHeader.vue';

const props = defineProps<{
  action: 'edit' | 'add';
}>();

const components = {
  UComboBox,
  UExtendingInput,
  UInputClassified,
  UInputCheckbox,
  UInputDate,
  UInputPassword,
  UInputText,
  UMultiInput,
  UMultiObjectSelect,
  UMultiSelect,
  USelect,
};

const {t} = useTranslation();
const route = useRoute();
const router = useRouter();

const standby = reactive(useStandby());
const errorStore = useErrorStore();

const nonModalError = ref('');
const fetchedObject = ref<EditViewConfig | null>(null);
const addViewConfigLoaded = ref(false);

interface FormElem {
  validate: () => void;
  isInvalid: boolean;
  focus: () => void;
  setCustomErrorMessage: (message: string) => void;
}
type FieldsetElems = Map<string, FormElem>;
type PageElems = Map<string, FieldsetElems>;
const formElems = ref<Map<string, PageElems>>(new Map());
const formElemsDirect = ref<Map<string, FormElem>>(new Map());
const refFormElem = (pageName: string, fieldsetName: string, propName: string, el: FormElem): void => {
  // If el is null, it will be ignored
  const _page = formElems.value.get(pageName) ?? (new Map() as PageElems);
  if (!formElems.value.has(pageName)) {
    formElems.value.set(pageName, _page);
  }
  const _fieldset = _page.get(fieldsetName) ?? (new Map() as FieldsetElems);
  if (!_page.has(fieldsetName)) {
    _page.set(fieldsetName, _fieldset);
  }
  _fieldset.set(propName, el);
  formElemsDirect.value.set(propName, el);
};

const disableActionButton = computed(() => {
  return !fields.value.some(field => field.props.access === 'write');
});

const getSchool = (): string => {
  let school = origValues.value.school || route.query.school || '';
  if (Array.isArray(school)) {
    school = school[0];
  }
  return school;
};

const getPagesWithAccessNoneMapped = (pages: Page[]): Page[] => {
  const _pages: Page[] = JSON.parse(JSON.stringify(pages));
  for (const page of _pages) {
    for (const fieldset of page.fieldsets) {
      for (const row of fieldset.rows) {
        const _row = Array.isArray(row) ? row : [row];
        for (const field of _row) {
          if (field.props.access === 'none') {
            field.type = 'UInputClassified';
            field.props = {
              label: field.props.label,
              name: field.props.name,
              description: field.props.description ?? '',
            };
          }
        }
      }
    }
  }
  return _pages;
};
const pages = ref<Page[]>([]);
const fields = computed(() => {
  const _fields = [];
  for (const page of pages.value) {
    for (const fieldset of page.fieldsets) {
      for (const row of fieldset.rows) {
        const _row = Array.isArray(row) ? row : [row];
        for (const field of _row) {
          _fields.push(field);
        }
      }
    }
  }
  return _fields;
});
// TODO log somewhere if we get widget definition from backend that we do not have
const fieldsFiltered = computed(() => fields.value.filter(x => Object.keys(components).includes(x.type)));
const getLabel = (fieldName: string): string =>
  fields.value.find(f => f.props.name === fieldName)?.props.label || fieldName;

const pageValidity = ref<Record<string, boolean>>({});
const pageLinks = computed(() =>
  pages.value.map(page => ({
    label: pageValidity.value[page.name] === false ? `${page.label} (!)` : page.label,
    isInvalid: pageValidity.value[page.name] === false,
    name: page.name,
    to: {
      ...route,
      params: {
        ...route.params,
        page: page.name,
      },
    },
  }))
);
const currentPage = computed(() => {
  const firstPage = pages.value[0]?.name ?? '';
  const wantedPage = route.params['page'];
  if (typeof wantedPage === 'string') {
    const _wantedPage = wantedPage.toLowerCase();
    const pageExists = pages.value.findIndex(page => page.name.toLowerCase() === _wantedPage) !== -1;
    if (pageExists) {
      return _wantedPage;
    }
  }
  return firstPage;
});

const origValues = ref<FormValues>({});
const currentValues = ref<FormValues>({});
const currentValuesFiltered = computed(() => {
  const values = JSON.parse(JSON.stringify(currentValues.value));
  return values;
});
const changedValues = computed(() => {
  const _changes: FormValues = {};
  for (const key in currentValuesFiltered.value) {
    if (JSON.stringify(currentValues.value[key]) !== JSON.stringify(origValues.value[key])) {
      _changes[key] = currentValues.value[key];
    }
  }
  return _changes;
});
const hasChangedValues = computed(() => Object.keys(changedValues.value).length > 0);

if (props.action === 'edit') {
  onMounted(async () => {
    const newId = route.params['id'];
    if (typeof newId !== 'string') {
      // This error is very difficult to reproduce in the browser.
      // Manually navigating to the bare /edit/ endpoint returns a 404.
      // We won't bother to handle it.
      console.log('EditView: got non-string URL param', newId);
      return;
    }
    const school = getSchool();
    if (!school) {
      errorStore.push({
        message: t('EditView.loading.schoolMissing'),
      });
      return;
    }
    nonModalError.value = '';
    const result = await standby.wrap(() => fetchEditViewConfig(newId, school));
    if (!result.ok) {
      switch (result.error.type) {
        case 'objectNotFound':
          nonModalError.value = t('EditView.notFound');
          break;
        case 'generic':
          errorStore.push({
            message: t('EditView.fetchObject.error', {msg: result.error.message}),
          });
          break;
      }
    } else {
      fetchedObject.value = result.value;
      pages.value = getPagesWithAccessNoneMapped(result.value.pages);
      const _origValues = JSON.parse(JSON.stringify(fetchedObject.value.user));
      for (const name in _origValues) {
        const value = _origValues[name];
        if (value === null) {
          const type = fields.value.find(f => f.props.name === name);
          if (type !== undefined) {
            _origValues[name] = defaultValue(type.type);
          }
        }
      }
      origValues.value = _origValues;
      currentValues.value = JSON.parse(JSON.stringify(_origValues));
    }
  });
}

if (props.action === 'add') {
  onMounted(async () => {
    const school = getSchool();
    if (!school) {
      errorStore.push({
        message: t('EditView.loading.schoolMissing'),
      });
      return;
    }
    const result = await standby.wrap(() => fetchAddViewConfig(school));
    if (!result.ok) {
      errorStore.push({
        title: t('ErrorModal.heading'),
        message: t('EditView.fetchAddViewConfig.error', {msg: result.error}),
      });
      return;
    }
    pages.value = getPagesWithAccessNoneMapped(result.value.pages);
    const _origValues: FormValues = {};
    for (const field of fieldsFiltered.value) {
      _origValues[field.props.name] = defaultValue(field.type);
    }
    _origValues['school'] = school;
    origValues.value = _origValues;
    currentValues.value = JSON.parse(JSON.stringify(_origValues));
    addViewConfigLoaded.value = true;
  });
}

const backModal = reactive({
  active: false,
  skip: false,
});
onBeforeRouteLeave(() => {
  if (!backModal.skip && hasChangedValues.value) {
    backModal.active = true;
    return false;
  }
  return true;
});
const tryBack = (refetchGrid = false): void => {
  const _route: RouteLocationRaw = {
    name: 'users',
  };
  if (refetchGrid) {
    _route.query = {
      refetch: 'true',
    };
  }
  router.push(_route);
};
const forceBack = (refetchGrid = false): void => {
  backModal.active = false;
  backModal.skip = true;
  tryBack(refetchGrid);
};

const accordionStates = ref<Record<string, boolean>>({});
const updateAccordionState = (name: string): void => {
  if (accordionStates.value[name] === undefined) {
    accordionStates.value[name] = false;
    return;
  }
  accordionStates.value[name] = !accordionStates.value[name];
};
const accordionOpen = (name: string): boolean =>
  accordionStates.value[name] === undefined || accordionStates.value[name] === true;

const validate = (resetCustomErrorMessage = true): boolean => {
  let firstInvalid: FormElem | null = null;
  let firstInvalidPage = '';
  for (const [page, pageElems] of formElems.value) {
    for (const [fieldset, fieldsetElems] of pageElems) {
      for (const [name, el] of fieldsetElems.entries()) {
        if (resetCustomErrorMessage) {
          const field = fields.value.filter(fld => fld.props.name === name)[0];
          // Fields without read/write access will put errors in the console
          // if we try to set the error message
          const shouldSetMessage = field && ['read', 'write'].includes(field.props?.access || '');
          if (shouldSetMessage) {
            el.setCustomErrorMessage('');
          }
        }
        el.validate();
        if (el.isInvalid) {
          pageValidity.value[page] = false;
          accordionStates.value[fieldset] = true;
          if (firstInvalid === null) {
            firstInvalid = el;
            firstInvalidPage = page;
          }
        }
      }
    }
  }
  if (firstInvalid !== null) {
    router.push({
      name: route.name ?? undefined,
      params: {
        ...route.params,
        page: firstInvalidPage,
      },
      query: route.query,
      hash: route.hash,
    });

    // TODO is this robust enough?
    // nextTick does not work if the `page` changes
    setTimeout(() => {
      firstInvalid?.focus();
    }, 0);
    return false;
  }
  return true;
};

const saveFailedModal = reactive<{
  active: boolean;
  error: SaveError | null;
}>({
  active: false,
  error: null,
});

const handleSaveError = (): void => {
  if (saveFailedModal.error?.type === 'fieldErrors') {
    const unwatch = watch(
      () => saveFailedModal.active,
      active => {
        if (!active) {
          if (saveFailedModal.error && saveFailedModal.error.type === 'fieldErrors') {
            for (const err of saveFailedModal.error.errors) {
              const field = formElemsDirect.value.get(err.field);
              if (field) {
                field.setCustomErrorMessage(err.message);
              }
            }
          }
          // FIXME `nextTick` since `validate` focuses the first invalid form element but `focus-trap`
          // from `UModal` would focus a different element afterwards
          nextTick(() => {
            validate(false);
          });
          unwatch();
        }
      },
      {
        flush: 'post',
      }
    );
  }
};

const saveSuccessModal = reactive<{
  active: boolean;
  name: string;
}>({
  active: false,
  name: '',
});

const save = async (): Promise<void> => {
  if (!validate()) {
    return;
  }
  if (!hasChangedValues.value) {
    tryBack();
    return;
  }
  if (fetchedObject.value === null) {
    console.debug('TODO error handling');
    return;
  }

  const id: string = fetchedObject.value.id;
  const result = await standby.wrap(() => updateUser(id, getSchool(), changedValues.value));

  if (!result.ok) {
    saveFailedModal.active = true;
    saveFailedModal.error = result.error;
    handleSaveError();
    return;
  }
  forceBack(true);
};

const add = async (): Promise<void> => {
  if (!validate()) {
    return;
  }

  const result = await standby.wrap(() => createUser(getSchool(), currentValuesFiltered.value));

  if (!result.ok) {
    saveFailedModal.active = true;
    saveFailedModal.error = result.error;
    handleSaveError();
    return;
  }

  saveSuccessModal.active = true;
  saveSuccessModal.name = result.value.user.id;
};

const heading = computed(() => {
  if (props.action === 'edit') {
    return `${t('EditView.heading.edit')} > ${route.params['id']}`;
  }
  return `${t('EditView.heading.add')}`;
});

const windowScroll = ref(0);
const updateScroll = (): void => {
  windowScroll.value = window.scrollY;
};
const scrollCallback = updateScroll;
onMounted(() => {
  window.addEventListener('scroll', scrollCallback, {passive: true});
  updateScroll();
});
onUnmounted(() => {
  window.removeEventListener('scroll', scrollCallback);
});
const formNavStickyTop = ref(-1);
const formNav = ref<HTMLElement | null>(null);
onMounted(() => {
  if (formNav.value === null) {
    return;
  }
  formNavStickyTop.value = formNav.value.offsetTop;
});

const getRow = (row: Field | Field[]): Field[] => {
  if (Array.isArray(row)) {
    return row;
  }
  return [row];
};

const confirmLanguageSwitchReload = computed(() => hasChangedValues.value);
</script>

<template>
  <SiteHeader :confirmReload="confirmLanguageSwitchReload" />
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
            v-if="action === 'add' && addViewConfigLoaded"
            :label="t('EditView.button.add')"
            icon="save"
            primary
            :disabled="disableActionButton"
            @click="add"
          />
          <UButton
            v-if="action === 'edit' && fetchedObject !== null"
            :label="t('EditView.button.save')"
            icon="save"
            primary
            :disabled="disableActionButton"
            @click="save"
          />
          <UButton
            :label="t('EditView.button.back')"
            @click="tryBack(false)"
          />
        </div>
      </div>
    </div>
    <div
      v-if="nonModalError !== ''"
      class="editView__notFoundError"
    >
      <UIcon icon="alert-circle" />
      <h1>{{ nonModalError }}</h1>
    </div>
    <div v-else>
      <form
        novalidate
        class="editView__form editView__form editView__form--navlessIfSinglePage"
        @submit.prevent="action === 'add' ? add() : save()"
      >
        <div
          ref="formNav"
          class="uContainer uCard editView__form__nav"
          :class="{
            'editView__form__nav--hidden': pageLinks.length === 0,
            'editView__form__nav--singlePage': pageLinks.length === 1,
          }"
          :style="`--local-top: ${formNavStickyTop}px`"
        >
          <RouterLink
            v-for="link in pageLinks"
            :key="link.name"
            :to="link.to"
            :aria-current="currentPage === link.name.toLowerCase() ? 'page' : undefined"
            class="editView__form__nav__link"
            :class="{'editView__form__nav__link--invalid': link.isInvalid}"
          >
            {{ link.label }}
          </RouterLink>
        </div>
        <div
          v-for="page in pages"
          v-show="page.name === currentPage"
          :key="page.name"
          class="editView__form__content uContainer"
        >
          <div class="editView__form__pageHeading">
            {{ page.label }}
          </div>
          <div
            v-for="fieldset in page.fieldsets"
            :key="fieldset.label"
          >
            <div
              class="editView__accordion"
              @click="updateAccordionState(fieldset.name)"
            >
              <div class="editView__accordion__label">
                {{ fieldset.label }}
              </div>
              <UIcon :icon="accordionOpen(fieldset.name) ? 'chevron-up' : 'chevron-down'" />
            </div>
            <UTransitionHeight>
              <div
                v-show="accordionOpen(fieldset.name)"
                class="editView__accordion__contentWrapper"
              >
                <div class="editView__accordion__content">
                  <div
                    v-for="(row, index) in fieldset.rows"
                    :key="index"
                    class="editView__form__row"
                  >
                    <component
                      :is="components[field.type]"
                      v-for="field in getRow(row)"
                      :key="field.props.name"
                      :ref="el => refFormElem(page.name, fieldset.name, field.props.name, el as unknown as FormElem)"
                      v-bind="field.props"
                      v-model:modelValue="currentValues[field.props.name]"
                    />
                  </div>
                </div>
              </div>
            </UTransitionHeight>
          </div>
        </div>
        <button
          class="sr-only"
          type="submit"
          tabindex="-1"
        >
          {{ t('EditView.button.save') }}
        </button>
      </form>
    </div>
    <UConfirmDialog
      v-model:active="backModal.active"
      :title="t('ConfirmBackModal.heading')"
      :confirmLabel="t('ConfirmBackModal.button.discard', {context: props.action})"
      :cancelLabel="t('ConfirmBackModal.button.continue', {context: props.action})"
      @confirm="forceBack(false)"
    >
      <template #description>
        <div>
          <p>
            {{ t('ConfirmBackModal.description', {context: props.action}) }}
          </p>
        </div>
      </template>
    </UConfirmDialog>
    <UConfirmDialog
      v-model:active="saveFailedModal.active"
      :title="t('EditViewSaveFailedModal.heading', {context: props.action})"
      :confirmLabel="t('EditViewSaveFailedModal.button.confirmation')"
      hideCancel
    >
      <template #description>
        <template v-if="saveFailedModal.error === null">
          <p>
            {{ t('EditViewSaveFailedModal.baseDescription', {context: props.action}) }}
          </p>
        </template>
        <template v-else-if="saveFailedModal.error.type === 'generic'">
          <p>
            {{ saveFailedModal.error.message }}
          </p>
        </template>
        <template v-else-if="saveFailedModal.error.type === 'objectNotFound'">
          <p>
            {{ t('EditViewSaveFailedModal.objectNotFound') }}
          </p>
        </template>
        <template v-else-if="saveFailedModal.error.type === 'permissionsError'">
          <p>
            {{ saveFailedModal.error.message }}
          </p>
        </template>
        <template v-else>
          <p>{{ t('EditViewSaveFailedModal.fieldErrors.description') }}</p>
          <ul>
            <li
              v-for="err in saveFailedModal.error.errors"
              :key="err.field"
            >
              {{ getLabel(err.field) }}: {{ err.message }}
            </li>
          </ul>
        </template>
      </template>
    </UConfirmDialog>
    <UConfirmDialog
      v-model:active="saveSuccessModal.active"
      :title="t('EditViewSaveSuccessModal.heading', {name: saveSuccessModal.name})"
      :confirmLabel="t('EditViewSaveSuccessModal.button.confirmation')"
      hideCancel
      @confirm="forceBack(true)"
    />
  </main>
  <UStandbyFullScreen :active="!!standby.active" />
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

  .editView__form
    max-width: 1140px
    margin: 0 auto
    padding: var(--layout-spacing-unit) calc(4 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit))
    display: flex
    grid-gap: calc(4 * var(--layout-spacing-unit))

  .editView__form__nav
    flex: 0 0 auto
    align-self: flex-start
    width: 33%
    position: sticky
    top: var(--local-top)
    display: flex
    flex-direction: column
    align-items: flex-start
    &--hidden
      visibility hidden
  .editView__form__nav__link
    font-size: var(--font-size-3)
    color: var(--font-color-contrast-middle)
    text-decoration: none
    &[aria-current]
      color: var(--font-color-contrast-high)
    &:hover,
    &[aria-current]
      text-decoration: underline
    &--invalid
      color: var(--font-color-error) !important

  .editView__form--navlessIfSinglePage .editView__form__nav--singlePage
    display: none
  .editView__form__content
    border-radius: var(--border-radius-container)
    flex: 1 1 auto
  .editView__form__pageHeading
    font-size: var(--font-size-1)
    line-height: var(--font-lineheight-header)
    font-weight: 600
    padding: calc(2 * var(--layout-spacing-unit))
  .editView__form__row
    display: grid
    grid-template-columns: 1fr 1fr
    grid-gap: 0 1rem
    margin-bottom: calc(2 * var(--layout-spacing-unit))

    > .uFormElement:not(.uInputCheckbox)
      &:nth-child(1)
        .uFormElement__labelBox,
        .uFormElement__inputBox
          grid-column: 1 / 2
      &:nth-child(2)
        .uFormElement__labelBox,
        .uFormElement__inputBox
          grid-column: 2 / 3
      display: contents
      .uFormElement__labelBox
        grid-row: 1 / 2
      .uFormElement__inputBox
        grid-row: 2 / 3
    > .uFormElement
      &.uInputCheckbox
        grid-row: 2 / 3
        &:only-child
          grid-column: 1 / 3
      &.uMultiObjectSelect,
      &.uMultiSelect,
      &.uMultiInput
        min-width: 1% // fix flex overflow
        &:only-child
          .uFormElement__labelBox
            grid-column: 1 / 3
          .uFormElement__inputBox
            grid-column: 1 / 3

  .uExtendingInput.uMultiInput__subElement
    display: flex
    flex-direction: column
    gap: var(--layout-spacing-unit)
    > .uFormElement
      flex: 1 1 auto

  .editView__accordion
    display: flex
    align-items: center
    padding: calc(2 * var(--layout-spacing-unit))
    --local-background: transparent
    background: var(--local-background)
    transition: background 250ms
    cursor: pointer
    border-top: 2px solid var(--bgc-content-body)
    user-select: none
    &:hover
      --local-background: var(--bgc-titlepane-hover)
    .uIcon
      margin-left: auto

  .editView__accordion__contentWrapper
    display: flex
    flex-direction: column
  .editView__accordion__content
    padding: var(--layout-spacing-unit) calc(2 * var(--layout-spacing-unit)) 0

  .editView__accordion__label
    font-size: var(--font-size-2)
    line-height: var(--font-lineheight-normal)
    font-weight: 600

  .editView__notFoundError
    display: flex
    flex-direction: column
    align-items: center
    margin-top: calc(6 * var(--layout-spacing-unit))

    .uIcon
      width: 7rem;
      height: 7rem;
      color: var(--font-color-contrast-low)
      margin-bottom: calc(2 * var(--layout-spacing-unit))


.uContainer
  background-color: var(--bgc-content-container)
.uCard
  padding: calc(2 * var(--layout-spacing-unit))
  border-radius: var(--border-radius-container)

.editView__saveSuccessModal__container
  display: flex
  align-items: end
.editView__saveSuccessModal__field
  flex: 1

.editView .listView__header
  padding: calc(4 * var(--layout-spacing-unit))
  margin: 0 auto
  max-width: 1140px

.editView .listView__header
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

#header ~ .editView
  padding-top: var(--layout-height-header)
  .editView__stickyHeader
    top: var(--layout-height-header)
</style>
