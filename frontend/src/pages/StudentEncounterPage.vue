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
            <div class="text-caption text-grey-7">{{ encounter.case.area }}</div>
          </div>
          <q-chip outline color="primary">
            {{ t('encounterStep', { current: encounter.sequence_no, total: 3 }) }}
          </q-chip>
        </div>

        <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
          <template #avatar><q-icon name="warning" color="negative" /></template>
          <div class="text-weight-medium">{{ t('errorTitle') }}</div>
          <div>{{ errorMessage }}</div>
          <template #action>
            <q-btn v-if="notFound" flat :label="t('studentReset')" @click="startOver" />
          </template>
        </q-banner>

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
              <template v-for="question in FRAMING_QUESTIONS" :key="question.key">
                <q-select
                  v-if="question.kind === 'gate'"
                  v-model="framingAnswers[question.key]"
                  :options="gateOptions"
                  :label="question.prompt"
                  :disable="isCommitted"
                  outlined
                  emit-value
                  map-options
                  clearable
                />
                <q-input
                  v-else
                  v-model="framingAnswers[question.key]"
                  :label="question.prompt"
                  :disable="isCommitted"
                  outlined
                  autogrow
                  type="textarea"
                />
              </template>
            </div>
          </q-card-section>
        </q-card>

        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">{{ t('commitmentTitle') }}</div>
            <div class="text-caption text-grey-7 q-mb-md">{{ t('commitmentHint') }}</div>

            <div class="row q-col-gutter-md">
              <q-select
                v-model="pattern"
                class="col-12 col-sm-6"
                :options="patternOptions"
                :label="t('commitmentPattern')"
                :disable="isCommitted"
                outlined
                emit-value
                map-options
              />
              <q-select
                v-model="gate"
                class="col-12 col-sm-6"
                :options="gateOptions"
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

        <div v-if="reveal" class="row justify-end">
          <q-btn color="primary" flat :label="t('revealNextCase')" @click="goToCases" />
        </div>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import RevealPanel from 'components/RevealPanel.vue';
import { ApiError } from 'boot/api';
import { GATES, PATTERNS, createCommitment, revealEncounter } from 'src/api/student';
import type { FramingAnswers, Gate, Pattern } from 'src/api/student';
import { FRAMING_QUESTIONS } from 'src/content/framing';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'StudentEncounterPage',
});

const { t } = useI18n();
const router = useRouter();
const store = useStudentStore();

const encounter = computed(() => store.encounter);
const reveal = computed(() => store.reveal);
const isCommitted = computed(() => store.commitment !== null);

const patternOptions = PATTERNS.map((value) => ({ label: value, value }));
const gateOptions = GATES.map((value) => ({ label: value, value }));

// Kept separate from `gate` below on purpose: the framing answer records the
// learner's own reading of the decision point, while the commitment gate is
// their formal choice. They may coincide but neither drives the other.
const framingAnswers = reactive<Record<string, string | null>>(
  Object.fromEntries(FRAMING_QUESTIONS.map((question) => [question.key, null])),
);

const pattern = ref<Pattern | null>(null);
const gate = ref<Gate | null>(null);

const committing = ref(false);
const revealing = ref(false);
const errorMessage = ref('');
const notFound = ref(false);

const canCommit = computed(() => pattern.value !== null && gate.value !== null);
const revealLabel = computed(() => (reveal.value ? t('revealAgain') : t('revealAction')));

function handle(error: unknown) {
  if (error instanceof ApiError) {
    notFound.value = error.status === 404;
    errorMessage.value = error.status === 404 ? t('errorNotYours') : error.detail;
    return;
  }
  notFound.value = false;
  errorMessage.value = t('errorUnexpected');
}

function collectFramingAnswers(): FramingAnswers {
  const answers: FramingAnswers = {};
  for (const question of FRAMING_QUESTIONS) {
    const value = framingAnswers[question.key];
    if (typeof value === 'string' && value.trim() !== '') {
      answers[question.key] = value.trim();
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
    handle(error);
  } finally {
    committing.value = false;
  }
}

async function requestReveal() {
  if (!encounter.value) {
    return;
  }

  revealing.value = true;
  errorMessage.value = '';
  try {
    // Always render what the server returns. Reveal is compute-or-fetch, so a
    // repeat call is the stored verdict, not a new one.
    store.setReveal(await revealEncounter(encounter.value.id));
  } catch (error) {
    handle(error);
  } finally {
    revealing.value = false;
  }
}

async function goToCases() {
  store.clearEncounter();
  await router.push('/student');
}

async function startOver() {
  store.reset();
  await router.push('/student');
}
</script>

<style scoped>
.encounter-page {
  max-width: 760px;
  margin: 0 auto;
}

.encounter-page__narrative {
  white-space: pre-wrap;
}
</style>
