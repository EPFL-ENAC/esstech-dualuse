<template>
  <q-page class="q-pa-md">
    <div class="researcher-comparison-set-page column q-gutter-md">
      <div class="text-h5">{{ t('researcherComparisonSetTitle') }}</div>

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
            <q-btn flat :label="t('errorRetry')" @click="errorMessage = ''" />
          </template>
        </q-banner>

        <!-- Step 1: build the comparison set. Explicit action, not
             automatic on load -- the same treatment Student's own reveal
             gets even though it too is pure computation over already-stored
             data with no new user input. -->
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
            </q-card-section>
          </q-card>

          <!-- Step 2: prediction, locked once submitted. -->
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 q-mb-xs">{{ t('researcherPredictionTitle') }}</div>
              <div class="text-caption text-grey-7 q-mb-md">
                {{ t('researcherPredictionHint') }}
              </div>

              <div class="column q-gutter-md">
                <q-select
                  v-model="predictionRank1"
                  :options="patternOptions"
                  :label="t('researcherPredictionRankLabel', { rank: 1 })"
                  :disable="isPredicted"
                  outlined
                  emit-value
                  map-options
                >
                  <template #option="{ itemProps, opt }">
                    <q-item v-bind="itemProps">
                      <q-item-section>
                        <q-item-label>{{ opt.label }}</q-item-label>
                        <q-item-label caption>{{ opt.description }}</q-item-label>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
                <q-select
                  v-model="predictionRank2"
                  :options="patternOptions"
                  :label="t('researcherPredictionRankLabel', { rank: 2 })"
                  :disable="isPredicted"
                  outlined
                  emit-value
                  map-options
                >
                  <template #option="{ itemProps, opt }">
                    <q-item v-bind="itemProps">
                      <q-item-section>
                        <q-item-label>{{ opt.label }}</q-item-label>
                        <q-item-label caption>{{ opt.description }}</q-item-label>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
                <q-select
                  v-model="predictionRank3"
                  :options="patternOptions"
                  :label="t('researcherPredictionRankOptional')"
                  :disable="isPredicted"
                  outlined
                  clearable
                  emit-value
                  map-options
                >
                  <template #option="{ itemProps, opt }">
                    <q-item v-bind="itemProps">
                      <q-item-section>
                        <q-item-label>{{ opt.label }}</q-item-label>
                        <q-item-label caption>{{ opt.description }}</q-item-label>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
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

          <!-- Step 3: reveal. -->
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

          <!-- Never shows on the normal path: requestCounterCase() already
               ran automatically inside requestReveal(). Manual retry for
               the two abnormal ways to land here -- that call failing, or
               a reload landing between reveal succeeding and the lookup
               resolving, since this page has no onMounted to resume it. -->
          <div
            v-if="researcherStore.reveal && !researcherStore.counterCase && !loadingCounterCase"
            class="row justify-end"
          >
            <q-btn
              color="primary"
              flat
              :label="t('contrastContinue')"
              @click="requestCounterCase"
            />
          </div>

          <!-- Step 4: contrast. -->
          <ContrastPanel
            v-if="researcherStore.counterCase"
            :counter-case="researcherStore.counterCase"
            :contrast="researcherStore.contrast"
            :submitting="submittingContrast"
            question-key="researcherContrastQuestion"
            @submit="requestSubmitContrast"
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

import { ApiError } from 'boot/api';
import {
  buildComparisonSet,
  getSetCounterCase,
  revealPredictionComparison,
  submitPrediction,
  submitSetContrast,
} from 'src/api/researcher';
import type { PredictionEntry } from 'src/api/researcher';
import type { Pattern } from 'src/api/student';
import { PATTERN_OPTIONS } from 'src/content/patterns';
import ContrastPanel from 'src/components/ContrastPanel.vue';
import RevealComparisonPanel from 'src/components/RevealComparisonPanel.vue';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'ResearcherComparisonSetPage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();

const errorMessage = ref('');
const buildingComparisonSet = ref(false);
const submittingPrediction = ref(false);
const revealing = ref(false);
const loadingCounterCase = ref(false);
const submittingContrast = ref(false);

const predictionRank1 = ref<Pattern | null>(null);
const predictionRank2 = ref<Pattern | null>(null);
const predictionRank3 = ref<Pattern | null>(null);

const patternOptions = PATTERN_OPTIONS.map((option) => ({
  label: option.label,
  value: option.id,
  description: option.description,
}));

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

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

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
    errorMessage.value = describe(error);
  } finally {
    buildingComparisonSet.value = false;
  }
}

async function requestSubmitPrediction() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  const predictions: PredictionEntry[] = [
    { rank: 1, pattern: predictionRank1.value as Pattern },
    { rank: 2, pattern: predictionRank2.value as Pattern },
  ];
  if (predictionRank3.value !== null) {
    predictions.push({ rank: 3, pattern: predictionRank3.value });
  }

  submittingPrediction.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setPrediction(await submitPrediction(sessionId, predictions));
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submittingPrediction.value = false;
  }
}

async function requestReveal() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  revealing.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setReveal(await revealPredictionComparison(sessionId));
    await requestCounterCase();
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    revealing.value = false;
  }
}

async function requestCounterCase() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  loadingCounterCase.value = true;
  errorMessage.value = '';
  try {
    const result = await getSetCounterCase(sessionId);
    researcherStore.setCounterCase(result);
    if (!result.has_counter_case) {
      // No question to ask: submit the open-area acknowledgement directly,
      // rather than waiting on a button click with nothing to click for.
      await requestSubmitContrast(null);
    }
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    loadingCounterCase.value = false;
  }
}

async function requestSubmitContrast(learnerResponse: string | null) {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  submittingContrast.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setContrast(await submitSetContrast(sessionId, learnerResponse));
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submittingContrast.value = false;
  }
}
</script>
