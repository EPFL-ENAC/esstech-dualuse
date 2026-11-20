<template>
  <q-page class="q-pa-md">
    <div class="researcher-comparison-set-page column q-gutter-md">
      <div class="text-h5">{{ t('researcherComparisonSetTitle') }}</div>

      <ResearcherSessionMissing v-if="!researcherStore.session" />

      <template v-else>
        <ErrorBanner v-if="errorMessage" :message="errorMessage">
          <template #action>
            <q-btn flat :label="t('errorRetry')" @click="errorMessage = ''" />
          </template>
        </ErrorBanner>

        <q-card v-if="!researcherStore.comparisonSet" flat bordered>
          <q-card-section>
            <div class="text-body1">{{ t('researcherComparisonSetIntro') }}</div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn
              color="primary"
              unelevated
              :label="
                buildingComparisonSet
                  ? t('researcherComparisonSetBuilding')
                  : t('researcherComparisonSetBuild')
              "
              :loading="buildingComparisonSet"
              @click="requestComparisonSet"
            />
          </q-card-actions>
        </q-card>

        <template v-else>
          <q-card flat bordered>
            <q-card-section>
              <div class="text-body1">
                {{
                  t('researcherComparisonSetCaseCount', {
                    count: researcherStore.comparisonSet.case_count,
                  })
                }}
              </div>
              <div v-if="researcherStore.comparisonSet.was_widened" class="text-body2 q-mt-xs">
                {{ t('researcherComparisonSetWidenedNotice') }}
              </div>

              <q-list separator>
                <q-item
                  v-for="c in researcherStore.comparisonSet.cases"
                  :key="c.case_id"
                  clickable
                  :to="`/researcher/comparison-set/cases/${c.case_id}`"
                >
                  <q-item-section>
                    <q-item-label>{{ c.title }}</q-item-label>
                    <CaseDomainLabel :domain="c.domain" />
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>
          </q-card>

          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 q-mb-xs">{{ t('researcherPredictionTitle') }}</div>
              <div class="text-caption text-grey-7 q-mb-md">
                {{ t('researcherPredictionHint') }}
              </div>

              <div class="column q-gutter-md">
                <PatternSelect
                  v-model="predictionRank1"
                  :label="t('researcherPredictionRankLabel', { rank: 1 })"
                  :disable="isPredicted"
                />
                <PatternSelect
                  v-model="predictionRank2"
                  :label="t('researcherPredictionRankLabel', { rank: 2 })"
                  :disable="isPredicted"
                />
                <PatternSelect
                  v-model="predictionRank3"
                  :label="t('researcherPredictionRankOptional')"
                  :disable="isPredicted"
                  clearable
                />
              </div>

              <div v-if="hasDuplicatePrediction" class="text-negative text-caption q-mt-sm">
                {{ t('researcherPredictionDuplicateError') }}
              </div>
            </q-card-section>

            <q-card-actions align="right">
              <div v-if="isPredicted" class="text-caption text-positive q-mr-sm">
                {{ t('researcherPredictionSaved') }}
              </div>
              <q-btn
                v-else
                color="primary"
                unelevated
                :label="
                  submittingPrediction
                    ? t('researcherPredictionSubmitting')
                    : t('researcherPredictionSubmit')
                "
                :loading="submittingPrediction"
                :disable="!canSubmitPrediction"
                @click="requestSubmitPrediction"
              />
            </q-card-actions>
          </q-card>

          <div v-if="isPredicted && !researcherStore.reveal" class="row justify-end">
            <q-btn
              color="primary"
              unelevated
              :label="revealing ? t('researcherRevealLoading') : t('researcherRevealAction')"
              :loading="revealing"
              @click="requestReveal"
            />
          </div>

          <RevealComparisonPanel v-if="researcherStore.reveal" :reveal="researcherStore.reveal" />

          <div v-if="counterCaseRetryNeeded" class="row justify-end">
            <q-btn
              color="primary"
              flat
              :label="t('contrastContinue')"
              @click="requestCounterCase"
            />
          </div>

          <ContrastPanel
            v-if="twinCounterCase"
            :counter-case="twinCounterCase"
            :contrast="researcherStore.contrast"
            :submitting="submittingContrast"
            :question="t('researcherContrastQuestion')"
            @submit="submitContrast"
          />

          <div v-if="researcherStore.contrast" class="row justify-end">
            <q-btn
              color="primary"
              unelevated
              :label="t('researcherTagContinue')"
              @click="router.push('/researcher/complete')"
            />
          </div>
        </template>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import CaseDomainLabel from 'components/CaseDomainLabel.vue';
import ContrastPanel from 'components/ContrastPanel.vue';
import ErrorBanner from 'components/ErrorBanner.vue';
import PatternSelect from 'components/PatternSelect.vue';
import ResearcherSessionMissing from 'components/ResearcherSessionMissing.vue';
import RevealComparisonPanel from 'components/RevealComparisonPanel.vue';
import { useErrorMessage } from 'src/composables/useApiError';
import { useRevealContrast } from 'src/composables/useRevealContrast';
import {
  buildComparisonSet,
  getSetCounterCase,
  revealPredictionComparison,
  submitPrediction,
  submitSetContrast,
} from 'src/api/researcher';
import type { PredictionEntry } from 'src/api/researcher';
import type { Pattern } from 'src/api/taxonomy';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'ResearcherComparisonSetPage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();
const errors = useErrorMessage();
const { errorMessage } = errors;

const buildingComparisonSet = ref(false);
const submittingPrediction = ref(false);

const predictionRank1 = ref<Pattern | null>(null);
const predictionRank2 = ref<Pattern | null>(null);
const predictionRank3 = ref<Pattern | null>(null);

const {
  revealing,
  submittingContrast,
  twinCounterCase,
  counterCaseRetryNeeded,
  requestReveal,
  requestCounterCase,
  submitContrast,
} = useRevealContrast({
  targetId: () => researcherStore.session?.id,
  store: researcherStore,
  api: {
    reveal: revealPredictionComparison,
    getCounterCase: getSetCounterCase,
    submitContrast: submitSetContrast,
  },
  errors,
});

const isPredicted = computed(() => researcherStore.prediction !== null);

const filledPredictions = computed(() =>
  [predictionRank1.value, predictionRank2.value, predictionRank3.value].filter(
    (pattern): pattern is Pattern => pattern !== null,
  ),
);

const hasDuplicatePrediction = computed(
  () => new Set(filledPredictions.value).size !== filledPredictions.value.length,
);

const canSubmitPrediction = computed(
  () =>
    predictionRank1.value !== null &&
    predictionRank2.value !== null &&
    !hasDuplicatePrediction.value,
);

async function requestComparisonSet() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  buildingComparisonSet.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setComparisonSet(await buildComparisonSet(sessionId));
  } catch (error) {
    errors.report(error);
  } finally {
    buildingComparisonSet.value = false;
  }
}

async function requestSubmitPrediction() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined || predictionRank1.value === null || predictionRank2.value === null) {
    return;
  }

  const predictions: PredictionEntry[] = [
    { rank: 1, pattern: predictionRank1.value },
    { rank: 2, pattern: predictionRank2.value },
  ];
  if (predictionRank3.value !== null) {
    predictions.push({ rank: 3, pattern: predictionRank3.value });
  }

  submittingPrediction.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setPrediction(await submitPrediction(sessionId, predictions));
  } catch (error) {
    errors.report(error);
  } finally {
    submittingPrediction.value = false;
  }
}
</script>
