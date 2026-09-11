<template>
  <q-page class="q-pa-md">
    <div class="intake-page column q-gutter-md">
      <div>
        <div class="text-h5">{{ t('intakeTitle') }}</div>
        <div class="text-caption text-grey-7">{{ t('intakeIntro') }}</div>
      </div>

      <q-banner class="bg-amber-1 text-amber-10" rounded dense>
        <template #avatar><q-icon name="science" color="amber-8" /></template>
        {{ PLACEHOLDER_NOTICE }}
      </q-banner>

      <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
        <template #avatar><q-icon name="warning" color="negative" /></template>
        <div class="text-weight-medium">{{ t('errorTitle') }}</div>
        <div>{{ errorMessage }}</div>
        <template #action>
          <q-btn flat :label="t('studentReset')" @click="startOver" />
        </template>
      </q-banner>

      <q-inner-loading :showing="loading" />

      <!-- Step 1: the three diagnostic items. -->
      <q-card v-if="store.step === 'diagnostic'" flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">{{ t('intakeDiagnosticTitle') }}</div>

          <div class="column q-gutter-lg">
            <div v-for="item in DIAGNOSTIC_ITEMS" :key="item.id">
              <div class="text-body1 q-mb-sm">{{ item.prompt }}</div>
              <q-option-group
                :model-value="store.diagnosticAnswers[item.id] ?? null"
                :options="toOptions(item)"
                type="radio"
                @update:model-value="(value) => store.setDiagnosticAnswer(item.id, value)"
              />
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="submitting ? t('intakeSubmitting') : t('intakeSubmit')"
            :loading="submitting"
            :disable="!diagnosticComplete"
            @click="sendDiagnostic"
          />
        </q-card-actions>
      </q-card>

      <!-- Step 2: the primer, shown only below the threshold. -->
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
            @click="store.setStep('comprehension')"
          />
        </q-card-actions>
      </q-card>

      <!-- Step 3: the single comprehension check. -->
      <q-card v-else-if="store.step === 'comprehension'" flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">{{ t('intakeComprehensionTitle') }}</div>
          <div class="text-caption text-grey-7 q-mb-md">{{ t('intakeOneAttempt') }}</div>
          <div class="text-body1 q-mb-sm">{{ COMPREHENSION_CHECK.prompt }}</div>
          <q-option-group
            v-model="comprehensionChoice"
            :options="toOptions(COMPREHENSION_CHECK)"
            type="radio"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="submitting ? t('intakeSubmitting') : t('intakeSubmit')"
            :loading="submitting"
            :disable="comprehensionChoice === null"
            @click="sendComprehension"
          />
        </q-card-actions>
      </q-card>

      <!-- Step 4: static correction after a wrong answer. Nothing resubmits. -->
      <q-card v-else-if="store.step === 'correction'" flat bordered>
        <q-card-section class="bg-orange-1">
          <div class="text-subtitle1">{{ TARGETED_CORRECTION.title }}</div>
        </q-card-section>
        <q-card-section>
          <div class="text-body1 intake-page__prose">{{ TARGETED_CORRECTION.body }}</div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="t('intakeContinue')"
            @click="store.setStep('done')"
          />
        </q-card-actions>
      </q-card>

      <!-- Step 5: done. -->
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

import { ApiError } from 'boot/api';
import { getIntake, submitComprehension, submitDiagnostic } from 'src/api/intake';
import { createSession } from 'src/api/student';
import {
  COMPREHENSION_CHECK,
  DIAGNOSTIC_ITEMS,
  MICRO_PRIMER,
  PLACEHOLDER_NOTICE,
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
// The session lives in the student store because the Student/Individual path
// reads it from there once this flow hands off.
const studentStore = useStudentStore();

const loading = ref(false);
const submitting = ref(false);
const starting = ref(false);
const errorMessage = ref('');

const comprehensionChoice = ref<string | null>(store.comprehensionAnswer);

const diagnosticComplete = computed(() =>
  DIAGNOSTIC_ITEMS.every((item) => store.diagnosticAnswers[item.id] !== undefined),
);

function toOptions(item: IntakeItem) {
  return item.options.map((option) => ({ label: option.label, value: option.value }));
}

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

/** Answers in item order: the API matches them to items by position. */
function orderedAnswers(): string[] {
  return DIAGNOSTIC_ITEMS.map((item) => store.diagnosticAnswers[item.id] ?? '');
}

async function ensureSession(): Promise<string | null> {
  if (studentStore.session) {
    return studentStore.session.id;
  }

  try {
    const created = await createSession();
    studentStore.setSession(created);
    store.reset();
    return created.id;
  } catch (error) {
    errorMessage.value = describe(error);
    return null;
  }
}

async function sendDiagnostic() {
  const answers = orderedAnswers();
  const sessionId = await ensureSession();
  if (sessionId === null) {
    return;
  }

  submitting.value = true;
  errorMessage.value = '';
  try {
    store.setDiagnostic(await submitDiagnostic(sessionId, answers));
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submitting.value = false;
  }
}

async function sendComprehension() {
  const sessionId = studentStore.session?.id;
  const answer = comprehensionChoice.value;
  if (sessionId === undefined || answer === null) {
    return;
  }

  submitting.value = true;
  errorMessage.value = '';
  try {
    store.comprehensionAnswer = answer;
    store.setComprehension(await submitComprehension(sessionId, answer));
  } catch (error) {
    errorMessage.value = describe(error);
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

  // TEMPORARY: M1 role/mode selection does not exist yet, so a finished intake
  // drops straight into Student/Individual. When M1 lands, this redirect is
  // what it replaces -- the session is already started, so M1 only has to
  // choose a route and mode rather than create anything.
  await router.push('/student');
}

function startOver() {
  store.reset();
  studentStore.reset();
  comprehensionChoice.value = null;
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
    comprehensionChoice.value = store.comprehensionAnswer;
  } catch (error) {
    // A 404 is the ordinary "no intake yet" case for a session that was
    // started but never got past the first step, so it is not surfaced.
    if (!(error instanceof ApiError) || error.status !== 404) {
      errorMessage.value = describe(error);
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.intake-page {
  max-width: 760px;
  margin: 0 auto;
}

.intake-page__prose {
  white-space: pre-wrap;
}
</style>
