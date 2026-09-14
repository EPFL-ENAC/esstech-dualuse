<template>
  <q-card flat bordered class="contrast-panel">
    <template v-if="counterCase.has_counter_case && counterCase.counter_case">
      <q-card-section>
        <div class="text-subtitle2 q-mb-sm">{{ t('contrastTwinTitle') }}</div>
        <q-chip outline color="primary">{{ gateLever?.label }}</q-chip>
        <div class="text-body1 q-mt-sm">
          {{ counterCase.counter_case.responsibility_posture_contrast }}
        </div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-subtitle2 q-mb-sm">{{ t(questionKey) }}</div>
        <q-input
          v-model="response"
          :label="t('contrastResponseLabel')"
          :disable="contrast !== null"
          outlined
          autogrow
          type="textarea"
        />
      </q-card-section>

      <q-card-actions align="right">
        <div v-if="contrast" class="text-caption text-positive q-mr-sm">
          {{ t('contrastSaved') }}
        </div>
        <q-btn
          v-else
          color="primary"
          unelevated
          :label="submitting ? t('contrastSubmitting') : t('contrastSubmit')"
          :loading="submitting"
          :disable="response.trim() === ''"
          @click="emit('submit', response.trim())"
        />
      </q-card-actions>
    </template>

    <template v-else>
      <q-card-section>
        <div class="text-body1">{{ t('contrastOpenAreaMessage') }}</div>
      </q-card-section>
    </template>
  </q-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import type { Gate } from 'src/api/student';
import { GATE_DISPLAY_BY_ID } from 'src/content/patterns';

defineOptions({
  name: 'ContrastPanel',
});

// Structural, not imported from api/student.ts: this is the minimal shape
// this component actually reads (has_counter_case, counter_case.{gate_lever,
// responsibility_posture_contrast}, contrast.learner_response -- nothing
// else). Both Student's CounterCaseResponse/ContrastResponse and
// Researcher's SetCounterCaseResponse/SetContrastResponse satisfy this
// already, so both routes can pass their own real response types here
// without an adapter.
interface ContrastPanelCounterCase {
  has_counter_case: boolean;
  counter_case: {
    gate_lever: Gate;
    responsibility_posture_contrast: string;
  } | null;
}

interface ContrastPanelContrast {
  learner_response: string | null;
}

const props = withDefaults(
  defineProps<{
    counterCase: ContrastPanelCounterCase;
    contrast: ContrastPanelContrast | null;
    submitting: boolean;
    /** i18n key for the reflection question, shown only on the twin
     * branch. Defaults to Student's own wording so this stays a no-op
     * for every existing call site. */
    questionKey?: string;
  }>(),
  { questionKey: 'contrastWhoQuestion' },
);
const emit = defineEmits<{ submit: [learnerResponse: string] }>();

const { t } = useI18n();

const response = ref(props.contrast?.learner_response ?? '');

// The component stays mounted across the submit (v-if="counterCase", not
// v-if="contrast"), so a losing concurrent submission on the same encounter
// still gets a 200 back with the winner's stored entry -- idempotency, same
// as reveal. Without this, `response` would keep showing this tab's own
// locally-typed text next to "Reflection saved." while the database holds
// someone else's.
watch(
  () => props.contrast,
  (value) => {
    if (value) {
      response.value = value.learner_response ?? '';
    }
  },
);

const gateLever = computed(() =>
  props.counterCase.counter_case
    ? GATE_DISPLAY_BY_ID[props.counterCase.counter_case.gate_lever]
    : null,
);
</script>

<style scoped></style>
