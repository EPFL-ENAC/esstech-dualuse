<template>
  <q-layout view="hHh LpR lFf" class="app-shell">
    <q-header class="app-header" :class="{ 'app-header--glass': glass }">
      <q-toolbar class="app-header__toolbar">
        <q-toolbar-title class="app-brand">
          <router-link to="/" class="app-brand__link">
            <img class="app-brand__logo" src="/dark-mirror-logo.png" alt="" />
          </router-link>
        </q-toolbar-title>
        <nav class="app-nav" aria-label="Main">
          <router-link
            v-if="!isLandingPage"
            to="/"
            class="app-nav__link"
            exact-active-class="is-active"
            >{{ t('navHome') }}</router-link
          >
          <router-link to="/start" class="app-nav__link" active-class="is-active">{{
            t('navStart')
          }}</router-link>
          <router-link to="/#how-it-works" class="app-nav__link">{{ t('navHow') }}</router-link>
        </nav>
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
        <div class="app-footer__links">
          <div class="app-footer__powered">{{ t('footerExplore') }}</div>
          <router-link to="/">{{ t('navHome') }}</router-link>
          <router-link to="/start">{{ t('navStart') }}</router-link>
          <router-link to="/#how-it-works">{{ t('navHow') }}</router-link>
        </div>
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import { LOCALE_NAMES, nextLocale, setLocale } from 'boot/i18n';

const { t } = useI18n();
const route = useRoute();

const otherLocaleLabel = computed(() => LOCALE_NAMES[nextLocale.value]);
const isLandingPage = computed(() => route.path === '/');

// On the landing page the header is glass over the video, then turns solid
// white once the video has scrolled out from under it.
const pastHero = ref(false);
const glass = computed(() => isLandingPage.value && !pastHero.value);

function updateHeader() {
  const hero = document.querySelector('.landing-hero');
  const header = document.querySelector('.app-header');
  pastHero.value =
    hero !== null && hero.getBoundingClientRect().bottom <= (header?.clientHeight ?? 0);
}

onMounted(() => {
  window.addEventListener('scroll', updateHeader, { passive: true });
  window.addEventListener('resize', updateHeader);
});
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateHeader);
  window.removeEventListener('resize', updateHeader);
});
watch(
  () => route.path,
  () => nextTick(updateHeader),
);

function toggleLocale() {
  setLocale(nextLocale.value);
}
</script>
