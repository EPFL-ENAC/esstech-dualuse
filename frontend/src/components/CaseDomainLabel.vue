<template>
  <q-chip class="case-domain-label" outline color="primary">
    {{ t('caseTechnologyDomainLabel') }}: {{ domain }}
  </q-chip>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Domain } from 'src/api/taxonomy';

defineOptions({ name: 'CaseDomainLabel' });

defineProps<{ domain: Domain }>();

const { t } = useI18n();
</script>

<style scoped>
.case-domain-label {
  max-width: 100%;
  height: auto;
  white-space: normal;
  text-align: left;
  font-size: var(--fs-xs);
  font-weight: var(--w-bold);
}
</style>
