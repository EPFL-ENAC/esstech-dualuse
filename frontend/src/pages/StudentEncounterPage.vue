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
              >
                <template #option="{ itemProps, opt }">
                  <q-item v-bind="itemProps">
                    <q-item-section>
                      <q-item-label>{{ opt.label }}</q-item-label>
                      <q-item-label caption class="encounter-page__option-caption">
                        {{ opt.description }}
                      </q-item-label>
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>
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

        <!-- Never shows on the normal path: requestCounterCase() already ran
             automatically inside requestReveal(). This is a manual retry for
             the two abnormal ways to land here -- that call failing, or a
             reload landing between reveal succeeding and the lookup
             resolving, since this page has no onMounted to resume it. -->
        <div v-if="reveal && !counterCase && !loadingCounterCase" class="row justify-end">
          <q-btn color="primary" flat :label="t('contrastContinue')" @click="requestCounterCase" />
        </div>

        <ContrastPanel
          v-if="counterCase"
          :counter-case="counterCase"
          :contrast="contrast"
          :submitting="submittingContrast"
          @submit="submitContrastReflection"
        />

        <q-card v-if="contrast" flat bordered>
          <q-card-section>
            <div class="text-body1">
              {{ t('anotherCaseProgress', { current: encounter.sequence_no, total: 3 }) }}
            </div>
          </q-card-section>
          <q-card-actions align="right">
            <template v-if="encounter.sequence_no < 3">
              <q-btn flat :label="t('anotherCaseNo')" @click="goToTemporaryLanding" />
              <q-btn color="primary" unelevated :label="t('anotherCaseYes')" @click="goToCases" />
            </template>
            <q-btn v-else flat :label="t('anotherCaseFinish')" @click="goToTemporaryLanding" />
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

import ContrastPanel from 'components/ContrastPanel.vue';
import RevealPanel from 'components/RevealPanel.vue';
import { ApiError } from 'boot/api';
import { createCommitment, getCounterCase, revealEncounter, submitContrast } from 'src/api/student';
import type { FramingAnswers, Gate, Pattern } from 'src/api/student';
import { FRAMING_QUESTIONS } from 'src/content/framing';
import { GATE_OPTIONS, PATTERN_OPTIONS } from 'src/content/patterns';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'StudentEncounterPage',
});

const { t } = useI18n();
const router = useRouter();
const store = useStudentStore();

const encounter = computed(() => store.encounter);
const reveal = computed(() => store.reveal);
const counterCase = computed(() => store.counterCase);
const contrast = computed(() => store.contrast);
const isCommitted = computed(() => store.commitment !== null);

// Display text only. `value` stays the backend enum ID, so commitment payloads
// are unchanged by the relabelling. No cast is needed: content/patterns.ts keys
// its records by Pattern/Gate, so a drifted id is a compile error there.
const patternOptions = PATTERN_OPTIONS.map((option) => ({
  label: option.label,
  value: option.id,
  description: option.description,
}));

// Shared with the framing gate question above on purpose: same enum, one set of
// labels. The two answers stay independent — only their wording is common.
const gateOptions = GATE_OPTIONS.map((option) => ({
  label: option.label,
  value: option.id,
}));

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
const loadingCounterCase = ref(false);
const submittingContrast = ref(false);
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
    await requestCounterCase();
  } catch (error) {
    handle(error);
  } finally {
    revealing.value = false;
  }
}

async function requestCounterCase() {
  if (!encounter.value) {
    return;
  }

  loadingCounterCase.value = true;
  errorMessage.value = '';
  try {
    const result = await getCounterCase(encounter.value.id);
    store.setCounterCase(result);
    if (!result.has_counter_case) {
      // No question to ask: submit the open-area acknowledgement directly,
      // rather than waiting on a button click with nothing to click for.
      await submitContrastReflection(null);
    }
  } catch (error) {
    handle(error);
  } finally {
    loadingCounterCase.value = false;
  }
}

async function submitContrastReflection(learnerResponse: string | null) {
  if (!encounter.value) {
    return;
  }

  submittingContrast.value = true;
  errorMessage.value = '';
  try {
    store.setContrast(await submitContrast(encounter.value.id, learnerResponse));
  } catch (error) {
    handle(error);
  } finally {
    submittingContrast.value = false;
  }
}

async function goToCases() {
  store.clearEncounter();
  await router.push('/student');
}

async function goToTemporaryLanding() {
  // TEMPORARY: M6 debrief does not exist yet. "No" must not be a silent
  // dead-end; this redirect is what M6's debrief replaces once it exists.
  await router.push('/student/complete');
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

.encounter-page__option-caption {
  white-space: normal;
}
</style>
