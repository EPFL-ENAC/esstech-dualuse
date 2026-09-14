<template>
  <q-page class="q-pa-md">
    <div class="researcher-comparison-set-page column q-gutter-md">
      <div class="text-h5">{{ t('researcherComparisonSetTitle') }}</div>

      <q-banner class="bg-orange-1 text-orange-10" rounded>
        <template #avatar><q-icon name="construction" color="orange-10" /></template>
        {{ t('researcherComparisonSetPlaceholderNotice') }}
      </q-banner>

      <q-card v-if="intakeStore.gate !== null" flat bordered>
        <q-card-section>
          <div class="text-caption text-grey-7">
            {{ t('researcherComparisonSetGateLabel') }}
          </div>
          <div class="text-body2">{{ gateLabel }}</div>
        </q-card-section>
        <q-card-section>
          <div class="text-caption text-grey-7">{{ t('contrastResponseLabel') }}</div>
          <div class="text-body2">{{ intakeStore.postureResponse }}</div>
        </q-card-section>
      </q-card>

      <div>
        <q-btn flat :label="t('goHome')" to="/" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { GATE_DISPLAY_BY_ID } from 'src/content/patterns';
import { useResearcherIntakeStore } from 'stores/researcherIntake';

defineOptions({
  name: 'ResearcherComparisonSetPage',
});

const { t } = useI18n();
const intakeStore = useResearcherIntakeStore();

const gateLabel = computed(() =>
  intakeStore.gate === null ? '' : GATE_DISPLAY_BY_ID[intakeStore.gate].label,
);
</script>
