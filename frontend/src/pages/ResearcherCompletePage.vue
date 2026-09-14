<template>
  <q-page class="q-pa-md">
    <div class="researcher-complete-page column q-gutter-md">
      <!-- UX only: landing here with no Researcher session is a broken
           bookmark/back-button case, not a security boundary -- the real
           enforcement is require_researcher_route server-side, already
           closed. -->
      <q-banner v-if="!researcherStore.session" class="bg-grey-2" rounded>
        {{ t('researcherSessionMissing') }}
        <template #action>
          <q-btn flat :label="t('sessionStart')" to="/start" />
        </template>
      </q-banner>

      <template v-else>
        <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
          <template #avatar><q-icon name="warning" color="negative" /></template>
          <div class="text-weight-medium">{{ t('errorTitle') }}</div>
          <div>{{ errorMessage }}</div>
          <template #action>
            <q-btn v-if="notFound" flat :label="t('researcherReset')" @click="startOver" />
          </template>
        </q-banner>

        <div v-else-if="loading" class="row items-center q-gutter-sm text-grey-7">
          <q-spinner size="24px" />
        </div>

        <template v-else-if="report">
          <div class="text-h5">{{ t('researcherCompleteTitle') }}</div>

          <q-card v-if="report.trace_completeness === 'in_progress'" flat bordered>
            <q-card-section>
              <div class="text-body1">{{ t('researcherCompleteNotYetBody') }}</div>
            </q-card-section>
          </q-card>

          <template v-else>
            <q-card v-if="hasMappingInfo" flat bordered>
              <q-card-section class="column q-gutter-sm">
                <div class="text-subtitle1">{{ t('researcherTagTitle') }}</div>

                <div v-if="report.domain">
                  <div class="text-body2 text-grey-7">{{ t('researcherTagDomainLabel') }}</div>
                  <div class="text-subtitle1">{{ report.domain }}</div>
                </div>

                <div v-if="report.functions && report.functions.length > 0">
                  <div class="text-body2 text-grey-7 q-mb-xs">
                    {{ t('researcherTagFunctionsLabel') }}
                  </div>
                  <div class="row q-gutter-xs">
                    <q-chip v-for="fn in report.functions" :key="fn" dense outline color="primary">
                      {{ FUNCTION_LABEL_BY_ID[fn] }}
                    </q-chip>
                  </div>
                </div>

                <div v-if="report.forms && report.forms.length > 0">
                  <div class="text-body2 text-grey-7 q-mb-xs">
                    {{ t('researcherTagFormsLabel') }}
                  </div>
                  <div class="row q-gutter-xs">
                    <q-chip v-for="form in report.forms" :key="form" dense outline color="primary">
                      {{ FORM_LABEL_BY_ID[form] }}
                    </q-chip>
                  </div>
                </div>
              </q-card-section>
            </q-card>

            <q-card v-if="report.gate" flat bordered>
              <q-card-section class="column q-gutter-sm">
                <div class="text-subtitle1">{{ t('researcherGateTitle') }}</div>
                <q-chip outline color="primary">
                  {{ GATE_DISPLAY_BY_ID[report.gate].label }}
                </q-chip>
                <div>
                  <div class="text-body2 text-grey-7">{{ t('researcherGatePostureHint') }}</div>
                  <div class="text-body1">{{ report.posture_response }}</div>
                </div>
              </q-card-section>
            </q-card>

            <q-card v-if="report.case_count !== undefined" flat bordered>
              <q-card-section class="column q-gutter-sm">
                <div>
                  <div class="text-body1">
                    {{ t('researcherComparisonSetCaseCount', { count: report.case_count }) }}
                  </div>
                  <div v-if="report.was_widened" class="text-body2 q-mt-xs">
                    {{ t('researcherComparisonSetWidenedNotice') }}
                  </div>
                </div>

                <div v-if="report.predictions && report.predictions.length > 0">
                  <div class="text-body2 text-grey-7 q-mb-xs">
                    {{ t('researcherRevealYourPredictions') }}
                  </div>
                  <div class="row q-gutter-xs">
                    <q-chip
                      v-for="entry in report.predictions"
                      :key="entry.rank"
                      dense
                      outline
                      color="primary"
                    >
                      {{ entry.rank }}. {{ PATTERN_DISPLAY_BY_ID[entry.pattern].label }}
                    </q-chip>
                  </div>
                </div>

                <div v-if="report.dominant_pattern">
                  <div class="text-body2 text-grey-7">{{ t('researcherRevealDominantLabel') }}</div>
                  <div class="text-subtitle1">
                    {{ PATTERN_DISPLAY_BY_ID[report.dominant_pattern].label }}
                  </div>
                </div>
                <div v-else-if="report.trace_completeness === 'zero_pattern'" class="text-body2">
                  {{ t('researcherRevealLowActivationMessage') }}
                </div>

                <div v-if="report.secondary_patterns && report.secondary_patterns.length > 0">
                  <div class="text-body2 text-grey-7 q-mb-xs">
                    {{ t('researcherRevealSecondaryLabel') }}
                  </div>
                  <div class="row q-gutter-xs">
                    <q-chip
                      v-for="pattern in report.secondary_patterns"
                      :key="pattern"
                      dense
                      outline
                      color="primary"
                    >
                      {{ PATTERN_DISPLAY_BY_ID[pattern].label }}
                    </q-chip>
                  </div>
                </div>

                <div v-if="report.top_prediction_is_dominant !== undefined" class="text-body2">
                  {{
                    t(
                      report.top_prediction_is_dominant
                        ? 'researcherRevealTopMatchesDominant'
                        : 'researcherRevealTopDoesNotMatchDominant',
                    )
                  }}
                </div>
              </q-card-section>
            </q-card>

            <q-card v-if="report.contrast_type" flat bordered>
              <q-card-section>
                <template v-if="report.contrast_type === 'twin_counter_case'">
                  <div class="text-subtitle2 q-mb-sm">{{ t('contrastTwinTitle') }}</div>
                  <q-chip v-if="report.gate_lever" outline color="primary">
                    {{ GATE_DISPLAY_BY_ID[report.gate_lever].label }}
                  </q-chip>
                  <div class="q-mt-sm">
                    <div class="text-caption text-grey-7">{{ t('contrastResponseLabel') }}</div>
                    <div class="text-body1">{{ report.learner_response }}</div>
                  </div>
                </template>
                <div v-else class="text-body2">{{ t('contrastOpenAreaMessage') }}</div>
              </q-card-section>
            </q-card>

            <q-card v-if="report.reflection_prompt_key" flat bordered>
              <q-card-section>
                <div class="text-body1">{{ t(report.reflection_prompt_key) }}</div>
              </q-card-section>
            </q-card>
          </template>

          <div class="row justify-end">
            <q-btn color="primary" unelevated :label="t('goHome')" to="/" />
          </div>
        </template>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { ApiError } from 'boot/api';
import { getResearcherSessionReport } from 'src/api/researcher';
import type { ResearcherSessionReport } from 'src/api/researcher';
import { GATE_DISPLAY_BY_ID, PATTERN_DISPLAY_BY_ID } from 'src/content/patterns';
import { FORM_LABEL_BY_ID, FUNCTION_LABEL_BY_ID } from 'src/content/researcher';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'ResearcherCompletePage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();

const report = ref<ResearcherSessionReport | null>(null);
const loading = ref(false);
const errorMessage = ref('');
const notFound = ref(false);

const hasMappingInfo = computed(() => {
  if (!report.value) {
    return false;
  }
  return (
    report.value.domain !== undefined ||
    (report.value.functions?.length ?? 0) > 0 ||
    (report.value.forms?.length ?? 0) > 0
  );
});

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
  if (!researcherStore.session) {
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  try {
    report.value = await getResearcherSessionReport(researcherStore.session.id);
  } catch (error) {
    handle(error);
  } finally {
    loading.value = false;
  }
}

function startOver() {
  researcherStore.reset();
  void router.push('/researcher/intake');
}

onMounted(() => {
  void loadReport();
});
</script>

<style scoped>
.researcher-complete-page {
  max-width: 760px;
  margin: 0 auto;
}
</style>
