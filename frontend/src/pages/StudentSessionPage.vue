<template>
  <q-page class="q-pa-md">
    <div class="student-page column q-gutter-md">
      <div>
        <div class="text-h5">{{ t('studentTitle') }}</div>
        <div class="text-subtitle2 text-grey-7">{{ t('studentIntro') }}</div>
      </div>

      <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
        <template #avatar><q-icon name="warning" color="negative" /></template>
        <div class="text-weight-medium">{{ t('errorTitle') }}</div>
        <div>{{ errorMessage }}</div>
        <template #action>
          <q-btn flat :label="t('errorRetry')" @click="retry" />
          <q-btn flat :label="t('studentReset')" @click="startOver" />
        </template>
      </q-banner>

      <q-card v-if="!store.session" flat bordered>
        <q-card-section class="row items-center justify-between">
          <div class="text-body1">{{ t('studentIntro') }}</div>
          <q-btn
            color="primary"
            unelevated
            :label="starting ? t('studentStarting') : t('studentStart')"
            :loading="starting"
            @click="startSession"
          />
        </q-card-section>
      </q-card>

      <template v-else>
        <div class="row items-center justify-between">
          <q-chip color="primary" text-color="white" icon="play_arrow">
            {{ t('studentSessionActive') }}
          </q-chip>
          <q-btn flat dense :label="t('studentReset')" @click="startOver" />
        </div>

        <div class="text-h6">{{ t('casesTitle') }}</div>

        <div v-if="loadingCases" class="row items-center q-gutter-sm text-grey-7">
          <q-spinner size="24px" />
          <span>{{ t('casesLoading') }}</span>
        </div>

        <q-banner v-else-if="candidates.length === 0" class="bg-grey-2" rounded>
          {{ t('casesEmpty') }}
        </q-banner>

        <div v-else class="column q-gutter-md">
          <q-card v-for="candidate in candidates" :key="candidate.id" flat bordered>
            <q-card-section>
              <div class="text-subtitle1">{{ candidate.title }}</div>
              <div class="text-caption text-grey-7">{{ candidate.area }}</div>
              <div class="text-body2 q-mt-sm student-page__narrative">
                {{ candidate.narrative_until_crossroads }}
              </div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="selectingId === candidate.id ? t('caseSelecting') : t('caseSelect')"
                :loading="selectingId === candidate.id"
                :disable="selectingId !== null"
                @click="askToSelect(candidate)"
              />
            </q-card-actions>
          </q-card>
        </div>
      </template>

      <q-dialog v-model="confirmOpen">
        <q-card style="min-width: 320px; max-width: 420px">
          <q-card-section>
            <div class="text-h6">{{ t('confirmSelectTitle') }}</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            {{ t('confirmSelectBody', { title: pendingCase?.title ?? '' }) }}
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat :label="t('confirmCancel')" @click="cancelSelection" />
            <q-btn
              color="primary"
              unelevated
              :label="t('confirmSelect')"
              @click="confirmSelection"
            />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { ApiError } from 'boot/api';
import { createEncounter, listCandidateCases } from 'src/api/student';
import type { CaseCandidate } from 'src/api/student';
import { createSession } from 'src/api/sessions';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'StudentSessionPage',
});

const { t } = useI18n();
const router = useRouter();
const store = useStudentStore();

const candidates = ref<CaseCandidate[]>([]);
const loadingCases = ref(false);
const starting = ref(false);
const selectingId = ref<string | null>(null);
const errorMessage = ref('');

// Selecting a case creates an encounter immediately, spending one of the
// session's three slots with no way to give it back, so the POST is gated
// behind an explicit confirmation rather than a single click.
const confirmOpen = ref(false);
const pendingCase = ref<CaseCandidate | null>(null);

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

async function startSession() {
  starting.value = true;
  errorMessage.value = '';
  try {
    store.setSession(await createSession());
    await loadCandidates();
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    starting.value = false;
  }
}

async function loadCandidates() {
  loadingCases.value = true;
  errorMessage.value = '';
  try {
    candidates.value = await listCandidateCases();
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    loadingCases.value = false;
  }
}

function askToSelect(candidate: CaseCandidate) {
  pendingCase.value = candidate;
  confirmOpen.value = true;
}

function cancelSelection() {
  confirmOpen.value = false;
  pendingCase.value = null;
}

async function confirmSelection() {
  const candidate = pendingCase.value;
  confirmOpen.value = false;
  pendingCase.value = null;
  if (candidate !== null) {
    await selectCase(candidate);
  }
}

async function selectCase(candidate: CaseCandidate) {
  if (!store.session) {
    return;
  }

  selectingId.value = candidate.id;
  errorMessage.value = '';
  try {
    store.setEncounter(await createEncounter(store.session.id, candidate.id));
    await router.push('/student/encounter');
  } catch (error) {
    const message = describe(error);
    // The session may have filled up or the case may already be taken, so the
    // list on screen is no longer trustworthy. Refresh first, then report:
    // loadCandidates clears errorMessage, so setting it earlier would be lost.
    await loadCandidates();
    errorMessage.value = message;
  } finally {
    selectingId.value = null;
  }
}

function startOver() {
  store.reset();
  candidates.value = [];
  errorMessage.value = '';
}

function retry() {
  errorMessage.value = '';
  if (store.session) {
    void loadCandidates();
  }
}

onMounted(() => {
  if (store.session) {
    void loadCandidates();
  }
});
</script>

<style scoped>
.student-page {
  max-width: 760px;
  margin: 0 auto;
}

.student-page__narrative {
  white-space: pre-wrap;
}
</style>
