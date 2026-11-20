<!-- UX only, not a security boundary: the backend enforces the Researcher
     route. -->
<template>
  <q-banner class="app-alert--info">
    {{ t('researcherSessionMissing') }}
    <template #action>
      <q-btn flat :label="t('sessionStart')" to="/start" />
    </template>
  </q-banner>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineOptions({ name: 'ResearcherSessionMissing' });

const { t } = useI18n();
</script>
