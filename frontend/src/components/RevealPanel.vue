<template>
  <q-card flat bordered class="reveal-panel">
    <q-card-section :class="`bg-${verdict.color} text-white`">
      <div class="text-h6">{{ t(verdict.label) }}</div>
      <div class="text-body2 q-mt-xs">{{ t(verdict.hint) }}</div>
    </q-card-section>

    <q-card-section>
      <div class="row q-col-gutter-md">
        <div class="col-12 col-sm-6">
          <div class="text-caption text-grey-7">{{ t('revealYourReading') }}</div>
          <div class="text-subtitle1">
            {{ reveal.commitment.pattern }} · {{ reveal.commitment.gate }}
          </div>
        </div>
        <div class="col-12 col-sm-6">
          <div class="text-caption text-grey-7">{{ t('revealMainPath') }}</div>
          <div class="text-subtitle1">
            {{ reveal.case.main_path_pattern }} · {{ reveal.case.main_path_gate }}
          </div>
        </div>
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section>
      <div class="text-subtitle2 q-mb-sm">{{ t('revealTitle') }}</div>
      <div class="text-body1 reveal-panel__narrative">{{ reveal.case.full_narrative }}</div>
    </q-card-section>

    <q-card-section v-if="reveal.case.source_references.length > 0">
      <div class="text-caption text-grey-7 q-mb-xs">{{ t('revealSources') }}</div>
      <ul class="q-my-none q-pl-md">
        <li v-for="source in reveal.case.source_references" :key="source" class="text-body2">
          {{ source }}
        </li>
      </ul>
    </q-card-section>

    <q-card-section class="text-caption text-grey-7">
      {{ t('revealAt', { at: revealedAt }) }}
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import type { MatchResult, RevealResponse } from 'src/api/student';

defineOptions({
  name: 'RevealPanel',
});

const props = defineProps<{ reveal: RevealResponse }>();

const { t } = useI18n();

const VERDICTS: Record<MatchResult, { color: string; label: string; hint: string }> = {
  match: { color: 'positive', label: 'matchMatch', hint: 'matchMatchHint' },
  partial_match: { color: 'warning', label: 'matchPartial', hint: 'matchPartialHint' },
  mismatch: { color: 'negative', label: 'matchMismatch', hint: 'matchMismatchHint' },
};

const verdict = computed(() => VERDICTS[props.reveal.match_result]);

const revealedAt = computed(() => new Date(props.reveal.revealed_at).toLocaleString());
</script>

<style scoped>
.reveal-panel__narrative {
  white-space: pre-wrap;
}
</style>
