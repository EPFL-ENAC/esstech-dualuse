<template>
  <q-page class="q-pa-md">
    <div class="intake-page column q-gutter-md">
      <div>
        <div class="text-h5">{{ t('intakeTitle') }}</div>
        <div class="text-caption text-grey-7">{{ t('intakeIntro') }}</div>
      </div>

      <ErrorBanner v-if="errorMessage" :message="errorMessage">
        <template #action>
          <q-btn flat :label="t('studentReset')" @click="startOver" />
        </template>
      </ErrorBanner>

      <q-inner-loading :showing="loading" />

      <q-card v-if="store.step === 'diagnostic'" flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">{{ t('intakeDiagnosticTitle') }}</div>

          <div class="column q-gutter-lg">
            <div v-for="item in DIAGNOSTIC_ITEMS" :key="item.id">
              <div class="text-body1 q-mb-sm">{{ item.prompt }}</div>
              <q-option-group
                :model-value="store.diagnosticAnswers[item.id] ?? null"
                :options="[...item.options]"
                :disable="store.diagnostic !== null"
                type="radio"
                @update:model-value="(value) => store.setDiagnosticAnswer(item.id, value)"
              />
            </div>
          </div>

          <q-banner
            v-if="store.diagnostic"
            class="q-mt-lg"
            :class="store.diagnosticPassed ? 'app-alert--success' : 'app-alert--warning'"
          >
            <template #avatar>
              <q-icon :name="store.diagnosticPassed ? 'check_circle' : 'tips_and_updates'" />
            </template>
            <div class="text-weight-bold">{{ t('intakeAnswerHintTitle') }}</div>
            <div class="q-mt-xs">{{ t('intakeAnswerHintIntro') }}</div>
            <ul class="intake-hint__answers">
              <li v-for="answer in correctAnswerHints" :key="answer">{{ answer }}</li>
            </ul>
            <div class="text-weight-medium">
              {{ store.diagnosticPassed ? t('intakeAnswersCorrect') : t('intakeAnswersReview') }}
            </div>
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            v-if="!store.diagnostic"
            color="primary"
            unelevated
            :label="submitting ? t('intakeSubmitting') : t('intakeCheckAnswers')"
            :loading="submitting"
            :disable="!diagnosticComplete"
            @click="sendDiagnostic"
          />
          <q-btn
            v-else
            color="primary"
            unelevated
            :label="t('intakeContinue')"
            @click="store.advance()"
          />
        </q-card-actions>
      </q-card>

      <q-card v-else-if="store.step === 'primer'" flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">{{ MICRO_PRIMER.title }}</div>
          <div class="text-body1 intake-page__prose">{{ MICRO_PRIMER.body }}</div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="t('intakePrimerContinue')"
            @click="store.advance()"
          />
        </q-card-actions>
      </q-card>

      <q-card v-else-if="store.step === 'comprehension'" flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">{{ t('intakeComprehensionTitle') }}</div>
          <div class="text-body1 q-mb-sm">{{ COMPREHENSION_CHECK.prompt }}</div>
          <q-option-group
            :model-value="store.comprehensionAnswer"
            :options="[...COMPREHENSION_CHECK.options]"
            :disable="store.comprehension !== null"
            type="radio"
            @update:model-value="(value) => store.setComprehensionAnswer(value)"
          />

          <template v-if="store.comprehension">
            <q-banner v-if="store.comprehension.correct" class="app-alert--success q-mt-lg">
              <template #avatar><q-icon name="check_circle" /></template>
              <div class="text-weight-medium">{{ t('intakeComprehensionCorrect') }}</div>
            </q-banner>
            <q-banner v-else class="app-alert--warning q-mt-lg">
              <template #avatar><q-icon name="tips_and_updates" /></template>
              <div class="text-weight-bold">{{ TARGETED_CORRECTION.title }}</div>
              <div class="q-mt-xs">{{ TARGETED_CORRECTION.body }}</div>
              <div class="q-mt-sm text-weight-medium">
                {{ t('intakeComprehensionCorrectAnswer', { answer: comprehensionCorrectLabel }) }}
              </div>
            </q-banner>
          </template>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            v-if="!store.comprehension"
            color="primary"
            unelevated
            :label="submitting ? t('intakeSubmitting') : t('intakeCheckAnswers')"
            :loading="submitting"
            :disable="store.comprehensionAnswer === null"
            @click="sendComprehension"
          />
          <q-btn
            v-else
            color="primary"
            unelevated
            :label="t('intakeContinue')"
            @click="store.advance()"
          />
        </q-card-actions>
      </q-card>

      <q-card v-else flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">{{ t('intakeDoneTitle') }}</div>
          <div class="text-body1">{{ t('intakeDoneBody') }}</div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="starting ? t('studentStarting') : t('intakeGoToCases')"
            :loading="starting"
            @click="goToStudentFlow"
          />
        </q-card-actions>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import ErrorBanner from 'components/ErrorBanner.vue';
import { isNotFound, useErrorMessage } from 'src/composables/useApiError';
import { getIntake, submitComprehension, submitDiagnostic } from 'src/api/intake';
import { createSession } from 'src/api/sessions';
import {
  COMPREHENSION_CHECK,
  DIAGNOSTIC_ITEMS,
  MICRO_PRIMER,
  TARGETED_CORRECTION,
} from 'src/content/intake';
import type { IntakeItem } from 'src/content/intake';
import { useIntakeStore } from 'stores/intake';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'IntakePage',
});

const { t } = useI18n();
const router = useRouter();
const store = useIntakeStore();
const studentStore = useStudentStore();
const { errorMessage, report } = useErrorMessage();

const loading = ref(false);
const submitting = ref(false);
const starting = ref(false);

const diagnosticComplete = computed(() =>
  DIAGNOSTIC_ITEMS.every((item) => store.diagnosticAnswers[item.id] !== undefined),
);

function optionLabel(item: IntakeItem, value: string | undefined): string {
  return item.options.find((option) => option.value === value)?.label ?? '';
}

const correctAnswerHints = computed(() =>
  DIAGNOSTIC_ITEMS.map((item, index) =>
    optionLabel(item, store.diagnostic?.correct_answers[index]),
  ),
);

const comprehensionCorrectLabel = computed(() =>
  optionLabel(COMPREHENSION_CHECK, store.comprehension?.correct_answer),
);

async function ensureSession(): Promise<string | null> {
  if (studentStore.session) {
    return studentStore.session.id;
  }

  try {
    const created = await createSession('student');
    studentStore.setSession(created);
    return created.id;
  } catch (error) {
    report(error);
    return null;
  }
}

async function sendDiagnostic() {
  // Answers in item order: the API matches them to items by position.
  const answers = DIAGNOSTIC_ITEMS.map((item) => store.diagnosticAnswers[item.id] ?? '');
  const sessionId = await ensureSession();
  if (sessionId === null) {
    return;
  }

  submitting.value = true;
  errorMessage.value = '';
  try {
    store.setDiagnostic(await submitDiagnostic(sessionId, answers));
  } catch (error) {
    report(error);
  } finally {
    submitting.value = false;
  }
}

async function sendComprehension() {
  const sessionId = studentStore.session?.id;
  const answer = store.comprehensionAnswer;
  if (sessionId === undefined || answer === null) {
    return;
  }

  submitting.value = true;
  errorMessage.value = '';
  try {
    store.setComprehension(await submitComprehension(sessionId, answer));
  } catch (error) {
    report(error);
  } finally {
    submitting.value = false;
  }
}

async function goToStudentFlow() {
  starting.value = true;
  const sessionId = await ensureSession();
  starting.value = false;
  if (sessionId === null) {
    return;
  }

  await router.push('/student');
}

function startOver() {
  studentStore.startOver();
  errorMessage.value = '';
}

onMounted(async () => {
  const sessionId = studentStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  // Recover an interrupted flow from the server rather than trusting the
  // persisted store alone: the store can be stale if a submission landed but
  // the response never arrived.
  loading.value = true;
  try {
    store.hydrate(await getIntake(sessionId));
  } catch (error) {
    // A 404 just means this session has no intake yet.
    if (!isNotFound(error)) {
      report(error);
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.intake-page {
  margin: 0 auto;
}
.intake-page__prose {
  white-space: pre-wrap;
}
.intake-hint__answers {
  margin: var(--space-3) 0;
  padding-left: var(--space-4);
}
.intake-hint__answers li + li {
  margin-top: var(--space-2);
}
</style>
