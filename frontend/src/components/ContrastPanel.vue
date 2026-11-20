<template>
  <q-card flat bordered class="contrast-panel">
    <q-card-section>
      <div class="text-subtitle2 q-mb-sm">{{ t('contrastTwinTitle') }}</div>
      <q-chip outline color="primary">
        {{ GATE_DISPLAY_BY_ID[counterCase.gate_lever].label }}
      </q-chip>
      <div class="text-body1 q-mt-sm">
        {{ counterCase.responsibility_posture_contrast }}
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section>
      <div class="text-subtitle2 q-mb-sm">{{ question }}</div>
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
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import type { CounterCaseInfo } from 'src/api/contrast';
import { GATE_DISPLAY_BY_ID } from 'src/content/patterns';

defineOptions({
  name: 'ContrastPanel',
});

const props = defineProps<{
  counterCase: CounterCaseInfo;
  contrast: { learner_response: string | null } | null;
  submitting: boolean;
  /** The reflection question, already translated. */
  question: string;
}>();
const emit = defineEmits<{ submit: [learnerResponse: string] }>();

const { t } = useI18n();

const response = ref(props.contrast?.learner_response ?? '');

// A losing concurrent submission still gets a 200 carrying the winner's
// stored entry; show that rather than this tab's locally-typed text.
watch(
  () => props.contrast,
  (value) => {
    if (value) {
      response.value = value.learner_response ?? '';
    }
  },
);
</script>
