<template>
  <q-page class="q-pa-md">
    <div class="route-choice-page column q-gutter-lg">
      <div class="route-choice-page__heading">
        <div class="route-choice-page__kicker">{{ t('routeChoiceKicker') }}</div>
        <div class="text-h5">{{ t('routeChoiceTitle') }}</div>
        <div class="text-subtitle2 text-grey-7">{{ t('routeChoiceIntro') }}</div>
      </div>

      <ErrorBanner v-if="errorMessage" :message="errorMessage">
        <template #action>
          <q-btn flat :label="t('errorRetry')" @click="chooseResearcher" />
        </template>
      </ErrorBanner>

      <div class="row q-col-gutter-md">
        <div class="col-12 col-sm-6">
          <q-card class="route-card" flat bordered>
            <q-card-section>
              <div class="route-card__icon"><FeatherIcon name="student" /></div>
              <div class="text-subtitle1">{{ t('studentTitle') }}</div>
              <div class="text-body2 text-grey-7 q-mt-xs">{{ t('studentIntro') }}</div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="t('routeChoiceStudentAction')"
                :disable="choosing"
                to="/intake"
              />
            </q-card-actions>
          </q-card>
        </div>

        <div class="col-12 col-sm-6">
          <q-card class="route-card" flat bordered>
            <q-card-section>
              <div class="route-card__icon"><FeatherIcon name="research" /></div>
              <div class="text-subtitle1">{{ t('routeChoiceResearcherLabel') }}</div>
              <div class="text-body2 text-grey-7 q-mt-xs">
                {{ t('routeChoiceResearcherHint') }}
              </div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="choosing ? t('routeChoiceStarting') : t('routeChoiceResearcherAction')"
                :loading="choosing"
                :disable="choosing"
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

import ErrorBanner from 'components/ErrorBanner.vue';
import FeatherIcon from 'components/FeatherIcon.vue';
import { useErrorMessage } from 'src/composables/useApiError';
import { createSession } from 'src/api/sessions';
import { useResearcherStore } from 'stores/researcher';

defineOptions({
  name: 'RouteChoicePage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();
const { errorMessage, report } = useErrorMessage();

const choosing = ref(false);

async function chooseResearcher() {
  choosing.value = true;
  errorMessage.value = '';
  try {
    researcherStore.setSession(await createSession('researcher'));
    await router.push('/researcher/intake');
  } catch (error) {
    report(error);
  } finally {
    choosing.value = false;
  }
}
</script>

<style scoped>
.route-choice-page {
  margin: 0 auto;
}
.route-choice-page__heading {
  max-width: 40.625rem;
  margin-bottom: var(--space-3);
}
.route-choice-page__kicker {
  margin-bottom: var(--space-3);
  color: var(--fg-muted);
  font-size: var(--fs-sm);
  font-weight: var(--w-bold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.route-choice-page__heading .text-subtitle2 {
  margin-top: var(--space-2);
  font-size: var(--fs-body);
  font-weight: var(--w-normal);
  line-height: var(--lh-relaxed);
}
.route-card {
  height: 100%;
  overflow: hidden;
  transition: border-color var(--t-base);
}
.route-card:hover {
  border-color: var(--fg);
}
.route-card .q-card__section {
  min-height: 13.75rem;
}
.route-card__icon {
  width: 3.5rem;
  height: 3.5rem;
  display: grid;
  place-items: center;
  margin-bottom: var(--space-5);
  border: var(--border-w) solid var(--border);
  border-radius: var(--radius);
  color: var(--primary);
  background: var(--bg-subtle);
}
.route-card .text-subtitle1 {
  font-size: var(--fs-h5);
  font-weight: var(--w-bold);
  line-height: 1.3;
}
</style>
