<template>
  <q-page class="q-pa-md">
    <div class="student-page column q-gutter-md">
      <div>
        <div class="text-h5">{{ t('studentTitle') }}</div>
        <div class="text-subtitle2 text-grey-7">{{ t('studentIntro') }}</div>
      </div>

      <ErrorBanner v-if="errorMessage" :message="errorMessage">
        <template #action>
          <q-btn flat :label="t('errorRetry')" @click="retry" />
          <q-btn flat :label="t('studentReset')" @click="startOver" />
        </template>
      </ErrorBanner>

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
              <CaseDomainLabel :domain="candidate.domain" />
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

import CaseDomainLabel from 'components/CaseDomainLabel.vue';
import ErrorBanner from 'components/ErrorBanner.vue';
import { useDescribeError, useErrorMessage } from 'src/composables/useApiError';
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
const { errorMessage, report } = useErrorMessage();

const candidates = ref<CaseCandidate[]>([]);
const loadingCases = ref(false);
const starting = ref(false);
const selectingId = ref<string | null>(null);

// Creating an encounter irreversibly spends one of the session's
// CASES_PER_SESSION slots, so it is gated behind an explicit confirmation.
const confirmOpen = ref(false);
const pendingCase = ref<CaseCandidate | null>(null);

const describe = useDescribeError();

async function startSession() {
  starting.value = true;
  errorMessage.value = '';
  try {
    store.setSession(await createSession('student'));
    await loadCandidates();
  } catch (error) {
    report(error);
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
    report(error);
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
    // The session may have filled up or the case been taken: refresh the list,
    // then report (loadCandidates clears errorMessage).
    await loadCandidates();
    errorMessage.value = message;
  } finally {
    selectingId.value = null;
  }
}

async function startOver() {
  store.startOver();
  candidates.value = [];
  errorMessage.value = '';
  await router.push('/intake');
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
  margin: 0 auto;
}

.student-page__narrative {
  white-space: pre-wrap;
}
</style>
