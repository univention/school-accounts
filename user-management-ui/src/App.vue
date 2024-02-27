<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

<script setup lang="ts">
import DefaultRouterView from '@/components/DefaultRouterView.vue';
</script>

<template>
  <DefaultRouterView :keepAlive="{include: 'ListView'}" />
</template>
