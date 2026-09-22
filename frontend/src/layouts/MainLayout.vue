<template>
  <q-layout view="hHh LpR lFf" class="app-shell">
    <q-header class="app-header">
      <q-toolbar class="app-header__toolbar">
        <q-toolbar-title class="app-brand">
          <router-link to="/" class="app-brand__link">
            <img class="app-brand__logo" src="/dark-mirror-logo.png" alt="" />
          </router-link>
        </q-toolbar-title>
        <q-btn
          class="app-header__locale"
          flat
          dense
          no-caps
          :aria-label="otherLocaleLabel"
          @click="toggleLocale"
        >
          <q-icon name="language" size="16px" />
          <span class="app-header__locale-label">{{ otherLocaleLabel }}</span>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <footer v-if="isLandingPage" class="app-footer">
      <div class="app-footer__main">
        <div class="app-footer__identity">
          <router-link to="/" class="app-footer__brand" aria-label="Dark Mirror">
            <img src="/dark-mirror-logo-light.png" alt="Dark Mirror" />
          </router-link>
          <p>{{ t('footerTagline') }}</p>
        </div>

        <div class="app-footer__partners-block">
          <div class="app-footer__powered">Powered by</div>
          <img class="app-footer__partners" src="/epfl-unil-light.png" alt="EPFL and Unil" />
        </div>
      </div>

      <div class="app-footer__bottom">
        <span>© 2026 Dark Mirror</span>
        <span>{{ t('footerPurpose') }}</span>
      </div>
    </footer>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import type { MessageLanguages } from 'boot/i18n';

const { t, locale } = useI18n();
const route = useRoute();

const otherLocale = computed<MessageLanguages>(() => (locale.value === 'en-US' ? 'fr' : 'en-US'));
const otherLocaleLabel = computed(() => (otherLocale.value === 'fr' ? 'Français' : 'English'));
const isLandingPage = computed(() => route.path === '/');

function toggleLocale() {
  // Captured once: otherLocale is a computed derived from locale.value,
  // so reading it again after the assignment below would re-evaluate
  // against the new locale and yield the opposite of the value just set.
  const next = otherLocale.value;
  locale.value = next;
  localStorage.setItem('app-locale', next);
}
</script>
