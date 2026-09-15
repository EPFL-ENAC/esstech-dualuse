<template>
  <q-page class="q-pa-md">
    <div class="researcher-case-detail-page column q-gutter-md">
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

        <div v-else-if="loading" class="row items-center q-gutter-sm text-grey-7">
          <q-spinner size="24px" />
        </div>

        <template v-else-if="detail">
          <div class="text-h5">{{ detail.title }}</div>

          <q-card flat bordered>
            <q-card-section>
              <div class="text-caption text-grey-7">{{ detail.area }}</div>
              <div class="text-body2 q-mt-sm">{{ detail.narrative_until_crossroads }}</div>
            </q-card-section>
          </q-card>

          <q-card flat bordered>
            <q-card-section class="column q-gutter-sm">
              <div class="text-subtitle1">{{ t('researcherTagTitle') }}</div>

              <div>
                <div class="text-body2 text-grey-7">{{ t('researcherTagDomainLabel') }}</div>
                <div class="text-subtitle1">{{ detail.domain }}</div>
              </div>

              <div v-if="detail.functions.length > 0">
                <div class="text-body2 text-grey-7 q-mb-xs">
                  {{ t('researcherTagFunctionsLabel') }}
                </div>
                <div class="row q-gutter-xs">
                  <q-chip v-for="fn in detail.functions" :key="fn" dense outline color="primary">
                    {{ FUNCTION_LABEL_BY_ID[fn] }}
                  </q-chip>
                </div>
              </div>

              <div v-if="detail.forms.length > 0">
                <div class="text-body2 text-grey-7 q-mb-xs">
                  {{ t('researcherTagFormsLabel') }}
                </div>
                <div class="row q-gutter-xs">
                  <q-chip v-for="form in detail.forms" :key="form" dense outline color="primary">
                    {{ FORM_LABEL_BY_ID[form] }}
                  </q-chip>
                </div>
              </div>

              <q-chip outline color="secondary">
                {{ t(INCLUSION_REASON_LABEL_KEY[detail.inclusion_reason]) }}
              </q-chip>
            </q-card-section>
          </q-card>

          <!-- Gated: absent (not null) until the session has a submitted
               prediction. Mirrors Student's own pre-reveal candidate card,
               which simply omits this content with no placeholder
               explanation. -->
          <q-card v-if="detail.main_path_pattern" flat bordered>
            <q-card-section>
              <div class="text-caption text-grey-7">{{ t('revealMainPath') }}</div>
              <div class="text-subtitle1">
                {{ PATTERN_DISPLAY_BY_ID[detail.main_path_pattern].label }}
              </div>
              <div v-if="detail.main_path_gate" class="text-subtitle1">
                {{ GATE_DISPLAY_BY_ID[detail.main_path_gate].label }}
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section v-if="detail.full_narrative">
              <div class="text-body1">{{ detail.full_narrative }}</div>
            </q-card-section>

            <q-card-section v-if="detail.source_references && detail.source_references.length > 0">
              <div class="text-caption text-grey-7 q-mb-xs">{{ t('revealSources') }}</div>
              <ul class="q-my-none q-pl-md">
                <li v-for="source in detail.source_references" :key="source" class="text-body2">
                  {{ source }}
                </li>
              </ul>
            </q-card-section>
          </q-card>

          <div class="row justify-end">
            <q-btn flat :label="t('researcherCaseDetailBack')" to="/researcher/comparison-set" />
          </div>
        </template>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import { ApiError } from 'boot/api';
import { getResearcherCaseDetail } from 'src/api/researcher';
import type { InclusionReason, ResearcherCaseDetail } from 'src/api/researcher';
import { GATE_DISPLAY_BY_ID, PATTERN_DISPLAY_BY_ID } from 'src/content/patterns';
import { FORM_LABEL_BY_ID, FUNCTION_LABEL_BY_ID } from 'src/content/researcher';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'ResearcherCaseDetailPage',
});

const { t } = useI18n();
const route = useRoute();
const researcherStore = useResearcherStore();

const detail = ref<ResearcherCaseDetail | null>(null);
const loading = ref(false);
const errorMessage = ref('');

const INCLUSION_REASON_LABEL_KEY: Record<InclusionReason, string> = {
  shared_function: 'researcherInclusionReasonSharedFunction',
  widened_by_domain: 'researcherInclusionReasonWidenedByDomain',
};

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

async function loadCaseDetail() {
  const sessionId = researcherStore.session?.id;
  const caseId = route.params.caseId;
  if (sessionId === undefined || typeof caseId !== 'string') {
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  try {
    detail.value = await getResearcherCaseDetail(sessionId, caseId);
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadCaseDetail();
});
</script>
