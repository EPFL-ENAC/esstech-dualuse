<template>
  <q-card flat bordered class="reveal-comparison-panel">
    <q-card-section>
      <div class="text-subtitle2 q-mb-sm">{{ t('researcherRevealTitle') }}</div>

      <template v-if="reveal.dominant_pattern !== null">
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-6">
            <div class="text-caption text-grey-7">
              {{ t('researcherRevealDominantLabel') }}
            </div>
            <div class="text-subtitle1">{{ dominantLabel }}</div>
          </div>
          <div v-if="secondaryLabels.length > 0" class="col-12 col-sm-6">
            <div class="text-caption text-grey-7">
              {{ t('researcherRevealSecondaryLabel') }}
            </div>
            <div class="text-subtitle1">{{ secondaryLabels.join(', ') }}</div>
          </div>
        </div>
      </template>
      <div v-else class="text-body1">
        {{ t('researcherRevealLowActivationMessage') }}
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section>
      <div class="text-caption text-grey-7 q-mb-xs">
        {{ t('researcherRevealYourPredictions') }}
      </div>
      <div v-for="entry in sortedPredictions" :key="entry.rank" class="text-body1">
        {{ entry.rank }}. {{ PATTERN_DISPLAY_BY_ID[entry.pattern].label }}
      </div>

      <div class="text-body1 q-mt-sm">
        {{
          reveal.top_prediction_is_dominant
            ? t('researcherRevealTopMatchesDominant')
            : t('researcherRevealTopDoesNotMatchDominant')
        }}
      </div>

      <div v-if="reveal.predictions_in_secondary.length > 0" class="q-mt-sm">
        <div class="text-caption text-grey-7">
          {{ t('researcherRevealInSecondaryLabel') }}
        </div>
        <div class="text-body2">{{ inSecondaryLabels.join(', ') }}</div>
      </div>

      <div v-if="reveal.predictions_not_activated.length > 0" class="q-mt-sm">
        <div class="text-caption text-grey-7">
          {{ t('researcherRevealNotActivatedLabel') }}
        </div>
        <div class="text-body2">{{ notActivatedLabels.join(', ') }}</div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import type { RevealComparison } from 'src/api/researcher';
import { PATTERN_DISPLAY_BY_ID } from 'src/content/patterns';

defineOptions({
  name: 'RevealComparisonPanel',
});

const props = defineProps<{ reveal: RevealComparison }>();

const { t } = useI18n();

const dominantLabel = computed(() =>
  props.reveal.dominant_pattern === null
    ? ''
    : PATTERN_DISPLAY_BY_ID[props.reveal.dominant_pattern].label,
);

const secondaryLabels = computed(() =>
  props.reveal.secondary_patterns.map((pattern) => PATTERN_DISPLAY_BY_ID[pattern].label),
);

const sortedPredictions = computed(() =>
  [...props.reveal.predictions].sort((a, b) => a.rank - b.rank),
);

const inSecondaryLabels = computed(() =>
  props.reveal.predictions_in_secondary.map((pattern) => PATTERN_DISPLAY_BY_ID[pattern].label),
);

const notActivatedLabels = computed(() =>
  props.reveal.predictions_not_activated.map((pattern) => PATTERN_DISPLAY_BY_ID[pattern].label),
);
</script>
