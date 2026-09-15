<template>
  <q-layout view="hHh LpR lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-toolbar-title> {{ t('appTitle') }} </q-toolbar-title>
        <q-btn flat dense :label="otherLocaleLabel" @click="toggleLocale" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import type { MessageLanguages } from 'boot/i18n';

const { t, locale } = useI18n();

const otherLocale = computed<MessageLanguages>(() => (locale.value === 'en-US' ? 'fr' : 'en-US'));
const otherLocaleLabel = computed(() => (otherLocale.value === 'fr' ? 'Français' : 'English'));

function toggleLocale() {
  // Captured once: otherLocale is a computed derived from locale.value,
  // so reading it again after the assignment below would re-evaluate
  // against the new locale and yield the opposite of the value just set.
  const next = otherLocale.value;
  locale.value = next;
  localStorage.setItem('app-locale', next);
}
</script>
