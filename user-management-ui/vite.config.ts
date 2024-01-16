// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {fileURLToPath, URL} from 'node:url';
import {defineConfig, type UserConfig} from 'vite';
import vue from '@vitejs/plugin-vue';

// https://github.com/vitejs/vite/issues/2245
import pluginRewriteAll from 'vite-plugin-rewrite-all';

// https://vitejs.dev/config/
export default defineConfig(async({mode}) => {  // eslint-disable-line @typescript-eslint/no-unused-vars
  const config: UserConfig = {
    plugins: [vue(), pluginRewriteAll()],
    base: '/',
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  };
  return config;
});
