<template>
  <q-page class="q-pa-md">
    <div class="complete-page column q-gutter-md">
      <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
        <template #avatar><q-icon name="warning" color="negative" /></template>
        <div class="text-weight-medium">{{ t('errorTitle') }}</div>
        <div>{{ errorMessage }}</div>
        <template #action>
          <q-btn v-if="notFound" flat :label="t('studentReset')" @click="startOver" />
        </template>
      </q-banner>

      <div v-else-if="loading" class="row items-center q-gutter-sm text-grey-7">
        <q-spinner size="24px" />
      </div>

      <template
        v-else-if="sessionReport && sessionReport.has_completed_cases && sessionReport.report"
      >
        <div>
          <div class="text-h5">{{ t('completeTitle') }}</div>
          <div class="text-subtitle2 text-grey-7">{{ t('completeBody') }}</div>
        </div>

        <q-card flat bordered>
          <q-card-section class="column q-gutter-sm">
            <div class="row justify-between">
              <div class="text-body2 text-grey-7">{{ t('completeCasesExploredLabel') }}</div>
              <div class="text-subtitle1">{{ sessionReport.report.cases_explored }}</div>
            </div>

            <div>
              <div class="text-body2 text-grey-7 q-mb-xs">
                {{ t('completeDecisionPointsLabel') }}
              </div>
              <div class="row q-gutter-xs">
                <q-chip
                  v-for="gate in sessionReport.report.decision_points_considered"
                  :key="gate"
                  dense
                  outline
                  color="primary"
                >
                  {{ GATE_DISPLAY_BY_ID[gate].label }}
                </q-chip>
              </div>
            </div>

            <div>
              <div class="text-body2 text-grey-7 q-mb-xs">
                {{ t('completePatternsSelectedLabel') }}
              </div>
              <div class="row q-gutter-xs">
                <q-chip
                  v-for="pattern in sessionReport.report.patterns_selected"
                  :key="pattern"
                  dense
                  outline
                  color="primary"
                >
                  {{ PATTERN_DISPLAY_BY_ID[pattern].label }}
                </q-chip>
              </div>
            </div>

            <div>
              <div class="text-body2 text-grey-7 q-mb-xs">
                {{ t('completeMatchBreakdownLabel') }}
              </div>
              <div class="row q-gutter-md">
                <div>
                  {{ t('matchMatch') }}: {{ sessionReport.report.match_result_counts.match }}
                </div>
                <div>
                  {{ t('matchPartial') }}:
                  {{ sessionReport.report.match_result_counts.partial_match }}
                </div>
                <div>
                  {{ t('matchMismatch') }}: {{ sessionReport.report.match_result_counts.mismatch }}
                </div>
              </div>
            </div>

            <div class="row justify-between">
              <div class="text-body2 text-grey-7">
                {{ t('completeCounterCaseReflectionsLabel') }}
              </div>
              <div class="text-subtitle1">
                {{ sessionReport.report.counter_case_reflections_completed }}
              </div>
            </div>

            <div v-if="sessionReport.report.scaffolding_depth">
              <div class="row justify-between">
                <div class="text-body2 text-grey-7">{{ t('scaffoldingLabel') }}</div>
                <div class="text-subtitle1">
                  {{ t(SCAFFOLDING_LABEL_KEY[sessionReport.report.scaffolding_depth]) }}
                </div>
              </div>
              <div class="text-caption text-grey-7">{{ t('scaffoldingPlaceholderNote') }}</div>
            </div>

            <div v-if="sessionReport.report.suggested_next_focus" class="row justify-between">
              <div class="text-body2 text-grey-7">{{ t('completeSuggestedFocusLabel') }}</div>
              <div class="text-subtitle1">
                {{ GATE_DISPLAY_BY_ID[sessionReport.report.suggested_next_focus].label }}
              </div>
            </div>
          </q-card-section>
        </q-card>

        <q-card
          v-for="(entry, index) in sessionReport.report.encounters"
          :key="index"
          flat
          bordered
        >
          <q-card-section :class="`bg-${verdictFor(entry.match_result).color} text-white`">
            <div class="text-h6">{{ entry.case_title }}</div>
            <div class="text-body2 q-mt-xs">{{ t(verdictFor(entry.match_result).label) }}</div>
          </q-card-section>

          <q-card-section>
            <div class="text-caption text-grey-7">{{ t('revealYourReading') }}</div>
            <div class="text-subtitle1">
              {{ PATTERN_DISPLAY_BY_ID[entry.committed_pattern].label }}
            </div>
            <div class="text-subtitle1">{{ GATE_DISPLAY_BY_ID[entry.committed_gate].label }}</div>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <div class="text-body1">{{ reflectionText(entry) }}</div>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <template v-if="entry.contrast_type === 'twin_counter_case'">
              <div class="text-subtitle2 q-mb-sm">{{ t('contrastTwinTitle') }}</div>
              <q-chip v-if="entry.gate_lever" outline color="primary">
                {{ GATE_DISPLAY_BY_ID[entry.gate_lever].label }}
              </q-chip>
            </template>
            <div v-else class="text-body2">{{ t('contrastOpenAreaMessage') }}</div>
          </q-card-section>
        </q-card>
      </template>

      <q-card v-else flat bordered>
        <q-card-section>
          <div class="text-body1">{{ t('completeNoCasesBody') }}</div>
        </q-card-section>
      </q-card>

      <div class="row justify-end">
        <q-btn color="primary" unelevated :label="t('completeGoHome')" @click="router.push('/')" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { ApiError } from 'boot/api';
import type { ScaffoldingDepth } from 'src/api/intake';
import { getSessionReport } from 'src/api/student';
import type { CompletedEncounterReport, MatchResult, SessionReport } from 'src/api/student';
import { GATE_DISPLAY_BY_ID, PATTERN_DISPLAY_BY_ID } from 'src/content/patterns';
import { useStudentStore } from 'stores/student';

defineOptions({
  name: 'StudentCompletePage',
});

const { t } = useI18n();
const router = useRouter();
const store = useStudentStore();

const sessionReport = ref<SessionReport | null>(null);
const loading = ref(false);
const errorMessage = ref('');
const notFound = ref(false);

const VERDICTS: Record<MatchResult, { color: string; label: string }> = {
  match: { color: 'positive', label: 'matchMatch' },
  partial_match: { color: 'warning', label: 'matchPartial' },
  mismatch: { color: 'negative', label: 'matchMismatch' },
};

function verdictFor(matchResult: MatchResult) {
  return VERDICTS[matchResult];
}

const SCAFFOLDING_LABEL_KEY: Record<ScaffoldingDepth, string> = {
  high: 'scaffoldingHigh',
  standard: 'scaffoldingStandard',
  low: 'scaffoldingLow',
};

const REFLECTION_KEY: Record<MatchResult, string> = {
  match: 'reflectionMatch',
  partial_match: 'reflectionPartialMatch',
  mismatch: 'reflectionMismatch',
};

function reflectionText(entry: CompletedEncounterReport): string {
  return t(REFLECTION_KEY[entry.match_result], {
    pattern: PATTERN_DISPLAY_BY_ID[entry.committed_pattern].label,
    gate: GATE_DISPLAY_BY_ID[entry.committed_gate].label,
  });
}

function handle(error: unknown) {
  if (error instanceof ApiError) {
    notFound.value = error.status === 404;
    errorMessage.value = error.status === 404 ? t('errorNotYours') : error.detail;
    return;
  }
  notFound.value = false;
  errorMessage.value = t('errorUnexpected');
}

async function loadReport() {
  if (!store.session) {
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  try {
    sessionReport.value = await getSessionReport(store.session.id);
  } catch (error) {
    handle(error);
  } finally {
    loading.value = false;
  }
}

function startOver() {
  store.reset();
  void router.push('/student');
}

onMounted(() => {
  void loadReport();
});
</script>

<style scoped>
.complete-page {
  max-width: 760px;
  margin: 0 auto;
}
</style>
