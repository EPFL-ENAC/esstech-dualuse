<template>
  <q-page class="q-pa-md">
    <div class="researcher-complete-page column q-gutter-md">
      <div class="text-h5">{{ t('researcherCompleteTitle') }}</div>

      <q-banner class="bg-orange-1 text-orange-10" rounded>
        <template #avatar><q-icon name="construction" color="orange-10" /></template>
        {{ t('researcherCompletePlaceholderNotice') }}
      </q-banner>

      <q-card v-if="researcherStore.contrast" flat bordered>
        <q-card-section>
          <div class="text-caption text-grey-7">{{ t('contrastResponseLabel') }}</div>
          <div class="text-body2">
            {{ researcherStore.contrast.learner_response ?? t('contrastOpenAreaMessage') }}
          </div>
        </q-card-section>
      </q-card>

      <div>
        <q-btn flat :label="t('goHome')" to="/" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'ResearcherCompletePage',
});

const { t } = useI18n();
const researcherStore = useResearcherStore();
</script>
