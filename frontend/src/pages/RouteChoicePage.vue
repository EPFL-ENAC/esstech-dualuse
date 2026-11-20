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
              <div class="route-card__icon"><q-icon name="school" size="28px" /></div>
              <div class="text-subtitle1">{{ t('studentTitle') }}</div>
              <div class="text-body2 text-grey-7 q-mt-xs">{{ t('studentIntro') }}</div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="t('routeChoiceStudentAction')"
                :disable="choosing"
                @click="chooseStudent"
              />
            </q-card-actions>
          </q-card>
        </div>

        <div class="col-12 col-sm-6">
          <q-card class="route-card" flat bordered>
            <q-card-section>
              <div class="route-card__icon route-card__icon--research">
                <q-icon name="biotech" size="28px" />
              </div>
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

function chooseStudent(): void {
  void router.push('/intake');
}

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
  max-width: 650px;
  margin-bottom: 14px;
}
.route-choice-page__kicker {
  margin-bottom: 14px;
  color: var(--du-coral);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.route-choice-page__heading .text-subtitle2 {
  margin-top: 12px;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.55;
}
.route-card {
  height: 100%;
  overflow: hidden;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}
.route-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 45px rgba(18, 32, 31, 0.1) !important;
}
.route-card .q-card__section {
  min-height: 220px;
}
.route-card__icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  margin-bottom: 38px;
  border-radius: 18px;
  color: var(--du-ink);
  background: var(--du-mint);
}
.route-card__icon--research {
  color: white;
  background: var(--du-blue);
}
.route-card .text-subtitle1 {
  font-family: var(--du-display);
  font-size: 25px;
  font-weight: 700;
  line-height: 1.15;
}
</style>
