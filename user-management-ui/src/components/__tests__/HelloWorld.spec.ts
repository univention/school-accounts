// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {describe, it, expect} from 'vitest';

import {mount} from '@vue/test-utils';
import HelloWorld from '../HelloWorld.vue';

describe('HelloWorld', () => {
  it('renders properly', () => {
    const wrapper = mount(HelloWorld, {props: {msg: 'Hello Vitest'}});
    expect(wrapper.text()).toContain('Hello Vitest');
  });
});
