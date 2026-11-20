<template>
  <q-page class="q-pa-md">
    <div class="encounter-page column q-gutter-md">
      <q-banner v-if="!encounter" class="bg-grey-2" rounded>
        {{ t('encounterMissing') }}
        <template #action>
          <q-btn flat :label="t('casesTitle')" @click="goToCases" />
        </template>
      </q-banner>

      <template v-else>
        <div class="row items-center justify-between">
          <div>
            <div class="text-h5">{{ encounter.case.title }}</div>
            <CaseDomainLabel :domain="encounter.case.domain" />
            <div class="text-caption text-grey-7">{{ encounter.case.area }}</div>
          </div>
          <q-chip outline color="primary">
            {{ t('encounterStep', { current: encounter.sequence_no, total: CASES_PER_SESSION }) }}
          </q-chip>
        </div>

        <ErrorBanner v-if="errorMessage" :message="errorMessage">
          <template v-if="notFound" #action>
            <q-btn flat :label="t('studentReset')" @click="startOver" />
          </template>
        </ErrorBanner>

        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2 q-mb-sm">{{ t('encounterTitle') }}</div>
            <div class="text-body1 encounter-page__narrative">
              {{ encounter.case.narrative_until_crossroads }}
            </div>
          </q-card-section>
        </q-card>

        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">{{ t('framingTitle') }}</div>
            <div class="text-caption text-grey-7 q-mb-md">{{ t('framingHint') }}</div>

            <div class="column q-gutter-md">
              <q-input
                v-for="question in FRAMING_QUESTIONS"
                :key="question.key"
                v-model="framingAnswers[question.key]"
                :label="question.prompt"
                :disable="isCommitted"
                outlined
                autogrow
                type="textarea"
              />
            </div>
          </q-card-section>
        </q-card>

        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">{{ t('commitmentTitle') }}</div>
            <div class="text-caption text-grey-7 q-mb-md">{{ t('commitmentHint') }}</div>

            <div class="row q-col-gutter-md">
              <PatternSelect
                v-model="pattern"
                class="col-12 col-sm-6"
                :label="t('commitmentPattern')"
                :disable="isCommitted"
              />
              <q-select
                v-model="gate"
                class="col-12 col-sm-6"
                :options="GATE_OPTIONS"
                :label="t('commitmentGate')"
                :disable="isCommitted"
                outlined
                emit-value
                map-options
              />
            </div>
          </q-card-section>

          <q-card-actions align="right">
            <div v-if="isCommitted" class="text-caption text-positive q-mr-sm">
              {{ t('commitmentSaved') }}
            </div>
            <q-btn
              v-else
              color="primary"
              unelevated
              :label="committing ? t('commitmentSubmitting') : t('commitmentSubmit')"
              :loading="committing"
              :disable="!canCommit"
              @click="submitCommitment"
            />
          </q-card-actions>
        </q-card>

        <div v-if="isCommitted" class="row justify-end q-gutter-sm">
          <q-btn
            color="primary"
            unelevated
            :label="revealing ? t('revealLoading') : revealLabel"
            :loading="revealing"
            @click="requestReveal"
          />
        </div>

        <RevealPanel v-if="reveal" :reveal="reveal" />

        <div v-if="counterCaseRetryNeeded" class="row justify-end">
          <q-btn color="primary" flat :label="t('contrastContinue')" @click="requestCounterCase" />
        </div>

        <ContrastPanel
          v-if="twinCounterCase"
          :counter-case="twinCounterCase"
          :contrast="contrast"
          :submitting="submittingContrast"
          :question="t('contrastWhoQuestion')"
          @submit="submitContrast"
        />

        <q-card v-if="contrast" flat bordered>
          <q-card-section>
            <div class="text-body1">
              {{
                t('anotherCaseProgress', {
                  current: encounter.sequence_no,
                  total: CASES_PER_SESSION,
                })
              }}
            </div>
          </q-card-section>
          <q-card-actions align="right">
            <template v-if="encounter.sequence_no < CASES_PER_SESSION">
              <q-btn flat :label="t('anotherCaseNo')" @click="goToDebrief" />
              <q-btn color="primary" unelevated :label="t('anotherCaseYes')" @click="goToCases" />
            </template>
            <q-btn v-else flat :label="t('anotherCaseFinish')" @click="goToDebrief" />
          </q-card-actions>
        </q-card>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import CaseDomainLabel from 'components/CaseDomainLabel.vue';
import ContrastPanel from 'components/ContrastPanel.vue';
import ErrorBanner from 'components/ErrorBanner.vue';
import PatternSelect from 'components/PatternSelect.vue';
import RevealPanel from 'components/RevealPanel.vue';
import { useOwnedResourceError } from 'src/composables/useApiError';
import { useRevealContrast } from 'src/composables/useRevealContrast';
import {
  CASES_PER_SESSION,
  createCommitment,
  getCounterCase,
  revealEncounter,
  submitContrast as submitContrastRequest,
} from 'src/api/student';
import type { FramingAnswers } from 'src/api/student';
import type { Gate, Pattern } from 'src/api/taxonomy';
import { FRAMING_QUESTIONS } from 'src/content/framing';
import { GATE_OPTIONS } from 'src/content/patterns';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'StudentEncounterPage',
});

const { t } = useI18n();
const errors = useOwnedResourceError();
const { errorMessage, notFound } = errors;
const router = useRouter();
const store = useStudentStore();

const encounter = computed(() => store.encounter);
const reveal = computed(() => store.reveal);
const contrast = computed(() => store.contrast);
const isCommitted = computed(() => store.commitment !== null);

const framingAnswers = reactive<Record<string, string>>(
  Object.fromEntries(FRAMING_QUESTIONS.map((question) => [question.key, ''])),
);

const pattern = ref<Pattern | null>(null);
const gate = ref<Gate | null>(null);

const committing = ref(false);

const {
  revealing,
  submittingContrast,
  twinCounterCase,
  counterCaseRetryNeeded,
  requestReveal,
  requestCounterCase,
  submitContrast,
} = useRevealContrast({
  targetId: () => store.encounter?.id,
  store,
  api: {
    reveal: revealEncounter,
    getCounterCase,
    submitContrast: submitContrastRequest,
  },
  errors,
});

const canCommit = computed(() => pattern.value !== null && gate.value !== null);
const revealLabel = computed(() => (reveal.value ? t('revealAgain') : t('revealAction')));

function collectFramingAnswers(): FramingAnswers {
  const answers: FramingAnswers = {};
  for (const question of FRAMING_QUESTIONS) {
    const value = framingAnswers[question.key]?.trim() ?? '';
    if (value !== '') {
      answers[question.key] = value;
    }
  }
  return answers;
}

async function submitCommitment() {
  if (!encounter.value || pattern.value === null || gate.value === null) {
    return;
  }

  committing.value = true;
  errorMessage.value = '';
  try {
    store.setCommitment(
      await createCommitment(encounter.value.id, {
        pattern: pattern.value,
        gate: gate.value,
        framing_answers: collectFramingAnswers(),
      }),
    );
  } catch (error) {
    errors.report(error);
  } finally {
    committing.value = false;
  }
}

async function goToCases() {
  store.clearEncounter();
  await router.push('/student');
}

async function goToDebrief() {
  await router.push('/student/complete');
}

async function startOver() {
  store.startOver();
  await router.push('/intake');
}
</script>

<style scoped>
.encounter-page {
  margin: 0 auto;
}

.encounter-page__narrative {
  white-space: pre-wrap;
}
</style>
