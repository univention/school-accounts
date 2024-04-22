// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import { test, expect } from '@playwright/test';


// See here how to get started:
// https://playwright.dev/docs/intro
test('visits the app root url', async ({ page }) => {
  await page.goto('/univention/ucsschool/user-management/ui/');
  if (process.env.CI_INTEGRATION) {
      await page.getByLabel('Username or email').fill('alex.admin');
      await page.getByLabel('Password').fill('univention');
      await page.getByLabel('Password').press('Enter');
  }
  await expect(page.getByRole('heading', { name: 'Users (schools)' })).toBeVisible();
})
