<template>
  <q-page class="q-pa-md">
    <div class="route-choice-page column q-gutter-md">
      <div>
        <div class="text-h5">{{ t('routeChoiceTitle') }}</div>
        <div class="text-subtitle2 text-grey-7">{{ t('routeChoiceIntro') }}</div>
      </div>

      <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
        <template #avatar><q-icon name="warning" color="negative" /></template>
        <div class="text-weight-medium">{{ t('errorTitle') }}</div>
        <div>{{ errorMessage }}</div>
        <template #action>
          <q-btn flat :label="t('errorRetry')" @click="retry" />
        </template>
      </q-banner>

      <div class="row q-col-gutter-md">
        <div class="col-12 col-sm-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1">{{ t('studentTitle') }}</div>
              <div class="text-body2 text-grey-7 q-mt-xs">{{ t('studentIntro') }}</div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="t('routeChoiceStudentAction')"
                :disable="choosing !== null"
                @click="chooseStudent"
              />
            </q-card-actions>
          </q-card>
        </div>

        <div class="col-12 col-sm-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1">{{ t('routeChoiceResearcherLabel') }}</div>
              <div class="text-body2 text-grey-7 q-mt-xs">
                {{ t('routeChoiceResearcherHint') }}
              </div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="
                  choosing === 'researcher'
                    ? t('routeChoiceStarting')
                    : t('routeChoiceResearcherAction')
                "
                :loading="choosing === 'researcher'"
                :disable="choosing !== null"
                @click="chooseResearcher"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { ApiError } from 'boot/api';
import { createSession } from 'src/api/sessions';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'RouteChoicePage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();

const choosing = ref<'researcher' | null>(null);
const errorMessage = ref('');
// Which action actually produced errorMessage, so the retry button
// re-invokes that action rather than assuming it's always the Researcher
// one. Only 'researcher' is reachable today (chooseStudent makes no network
// call and cannot fail), but retry() dispatches on this rather than
// hardcoding that.
const failedAction = ref<'researcher' | null>(null);

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

function chooseStudent(): void {
  // No POST here: IntakePage.vue's own ensureSession() lazily creates the
  // Student-route session on the first diagnostic submission, exactly as it
  // does today. This screen changes nothing about that timing.
  void router.push('/intake');
}

async function chooseResearcher() {
  choosing.value = 'researcher';
  errorMessage.value = '';
  failedAction.value = null;
  try {
    researcherStore.setSession(await createSession('researcher'));
    await router.push('/researcher/intake');
  } catch (error) {
    errorMessage.value = describe(error);
    failedAction.value = 'researcher';
  } finally {
    choosing.value = null;
  }
}

function retry(): void {
  if (failedAction.value === 'researcher') {
    void chooseResearcher();
  }
}
</script>
