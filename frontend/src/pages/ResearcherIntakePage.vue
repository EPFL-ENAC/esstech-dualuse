<template>
  <q-page class="q-pa-md">
    <div class="researcher-intake-page column q-gutter-md">
      <div class="text-h5">{{ t('researcherIntakeTitle') }}</div>

      <!-- UX only: landing here with no Researcher session is a broken
           bookmark/back-button case, not a security boundary -- the real
           enforcement is require_researcher_route server-side, already
           closed this session. -->
      <q-banner v-if="!researcherStore.session" class="bg-grey-2" rounded>
        {{ t('researcherSessionMissing') }}
        <template #action>
          <q-btn flat :label="t('sessionStart')" to="/start" />
        </template>
      </q-banner>

      <template v-else>
        <q-inner-loading :showing="loading" />

        <q-banner v-if="errorMessage" class="bg-red-1 text-negative" rounded>
          <template #avatar><q-icon name="warning" color="negative" /></template>
          <div class="text-weight-medium">{{ t('errorTitle') }}</div>
          <div>{{ errorMessage }}</div>
          <template #action>
            <q-btn flat :label="t('errorRetry')" @click="errorMessage = ''" />
          </template>
        </q-banner>

        <!-- Step 1: the free-text technology description. -->
        <q-card v-if="intakeStore.step === 'description'" flat bordered>
          <q-card-section>
            <div class="text-body1 q-mb-sm">{{ t('researcherDescriptionIntro') }}</div>
            <div class="text-caption text-grey-7 q-mb-md">
              {{ t('researcherDescriptionHint') }}
            </div>
            <q-input
              v-model="descriptionInput"
              type="textarea"
              autogrow
              filled
              :label="t('researcherDescriptionLabel')"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn
              color="primary"
              unelevated
              :label="
                submittingDescription
                  ? t('researcherDescriptionSubmitting')
                  : t('researcherDescriptionSubmit')
              "
              :loading="submittingDescription"
              :disable="!descriptionInput.trim()"
              @click="submitDescription"
            />
          </q-card-actions>
        </q-card>

        <!-- Step 2: Function/Form/Domain tagging, bounded to two attempts. -->
        <q-card v-else-if="intakeStore.step === 'tagging'" flat bordered>
          <template v-if="intakeStore.mappingStatus === 'mapped'">
            <q-card-section>
              <div class="text-subtitle1">{{ t('researcherTagMappedTitle') }}</div>
              <div class="text-body1 q-mt-sm">{{ t('researcherTagMappedBody') }}</div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="t('researcherTagContinue')"
                @click="intakeStore.setStep('gate-and-posture')"
              />
            </q-card-actions>
          </template>
          <template v-else>
            <q-card-section>
              <div class="text-subtitle1 q-mb-xs">{{ t('researcherTagTitle') }}</div>
              <div class="text-caption text-grey-7 q-mb-md">{{ t('researcherTagIntro') }}</div>

              <q-banner v-if="intakeStore.hasAttemptedTag" class="bg-grey-2 q-mb-md" rounded dense>
                <div>{{ t('researcherTagPartialNotice') }}</div>
                <div class="text-caption q-mt-xs">
                  {{ t('researcherTagAttemptRemaining') }}
                </div>
              </q-banner>

              <q-select
                v-model="domainInput"
                :options="DOMAIN_OPTIONS"
                :label="t('researcherTagDomainLabel')"
                filled
                clearable
                class="q-mb-md"
              />
              <q-select
                v-model="functionsInput"
                :options="functionOptions"
                :label="t('researcherTagFunctionsLabel')"
                filled
                multiple
                emit-value
                map-options
                class="q-mb-md"
              />
              <q-select
                v-model="formsInput"
                :options="formOptions"
                :label="t('researcherTagFormsLabel')"
                filled
                multiple
                emit-value
                map-options
              />
            </q-card-section>
            <q-card-actions align="right">
              <q-btn
                color="primary"
                unelevated
                :label="
                  submittingTag
                    ? t('researcherTagSubmitting')
                    : intakeStore.hasAttemptedTag
                      ? t('researcherTagRetry')
                      : t('researcherTagSubmit')
                "
                :loading="submittingTag"
                @click="submitTagAttempt"
              />
            </q-card-actions>
          </template>
        </q-card>

        <!-- Step 3: bounded retry exhausted, not mapped. Terminal: no
             retry button exists here, matching that submitTag itself
             hard-rejects a third attempt. -->
        <q-card v-else-if="intakeStore.step === 'exhausted'" flat bordered>
          <q-card-section>
            <div class="text-subtitle1">{{ t('researcherTagExhaustedTitle') }}</div>
            <div class="text-body1 q-mt-sm">{{ t('researcherTagExhaustedBody') }}</div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat :label="t('goHome')" to="/" />
          </q-card-actions>
        </q-card>

        <!-- Step 4: decision gate and responsibility posture. -->
        <q-card v-else-if="intakeStore.step === 'gate-and-posture'" flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-xs">{{ t('researcherGateTitle') }}</div>
            <div class="text-caption text-grey-7 q-mb-md">{{ t('researcherGateIntro') }}</div>

            <q-select
              v-model="gateInput"
              :options="gateOptions"
              :label="t('researcherGateQuestion')"
              filled
              emit-value
              map-options
              class="q-mb-md"
            />
            <q-input
              v-model="postureInput"
              type="textarea"
              autogrow
              filled
              :label="t('contrastResponseLabel')"
              :hint="t('researcherGatePostureHint')"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn
              color="primary"
              unelevated
              :label="submittingGate ? t('researcherGateSubmitting') : t('researcherGateSubmit')"
              :loading="submittingGate"
              :disable="gateInput === null || !postureInput.trim()"
              @click="submitGateAndPosture"
            />
          </q-card-actions>
        </q-card>

        <!-- Step 5: done. -->
        <q-card v-else flat bordered>
          <q-card-section>
            <div class="text-subtitle1">{{ t('researcherGateDoneTitle') }}</div>
            <div class="text-body1 q-mt-sm">{{ t('researcherGateDoneBody') }}</div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn
              color="primary"
              unelevated
              :label="t('researcherTagContinue')"
              @click="router.push('/researcher/comparison-set')"
            />
          </q-card-actions>
        </q-card>
      </template>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { ApiError } from 'boot/api';
import {
  createTechnologyIntake,
  getTechnologyIntake,
  setGateAndPosture as setGateAndPostureRequest,
  submitTag as submitTagRequest,
} from 'src/api/researcher';
import type { Domain, Form, Function } from 'src/api/researcher';
import type { Gate } from 'src/api/student';
import { DOMAIN_OPTIONS, FORM_OPTIONS, FUNCTION_OPTIONS } from 'src/content/researcher';
import { GATE_OPTIONS } from 'src/content/patterns';
import { useResearcherStore } from 'stores/researcher';
import { useResearcherIntakeStore } from 'stores/researcherIntake';

defineOptions({
  name: 'ResearcherIntakePage',
});

const { t } = useI18n();
const router = useRouter();
const researcherStore = useResearcherStore();
const intakeStore = useResearcherIntakeStore();

const loading = ref(false);
const errorMessage = ref('');

const descriptionInput = ref('');
const submittingDescription = ref(false);

const domainInput = ref<Domain | null>(null);
const functionsInput = ref<Function[]>([]);
const formsInput = ref<Form[]>([]);
const submittingTag = ref(false);

const gateInput = ref<Gate | null>(null);
const postureInput = ref('');
const submittingGate = ref(false);

const functionOptions = FUNCTION_OPTIONS.map((option) => ({
  label: option.label,
  value: option.id,
}));
const formOptions = FORM_OPTIONS.map((option) => ({ label: option.label, value: option.id }));
const gateOptions = GATE_OPTIONS.map((option) => ({ label: option.label, value: option.id }));

function describe(error: unknown): string {
  return error instanceof ApiError ? error.detail : t('errorUnexpected');
}

async function submitDescription() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  submittingDescription.value = true;
  errorMessage.value = '';
  try {
    intakeStore.setIntakeCreated(
      await createTechnologyIntake(sessionId, descriptionInput.value.trim()),
    );
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submittingDescription.value = false;
  }
}

async function submitTagAttempt() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  submittingTag.value = true;
  errorMessage.value = '';
  try {
    intakeStore.setTagResult(
      await submitTagRequest(sessionId, {
        domain: domainInput.value,
        functions: functionsInput.value,
        forms: formsInput.value,
      }),
    );
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submittingTag.value = false;
  }
}

async function submitGateAndPosture() {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined || gateInput.value === null) {
    return;
  }

  submittingGate.value = true;
  errorMessage.value = '';
  try {
    intakeStore.setGateAndPosture(
      await setGateAndPostureRequest(sessionId, {
        gate: gateInput.value,
        posture_response: postureInput.value.trim(),
      }),
    );
  } catch (error) {
    errorMessage.value = describe(error);
  } finally {
    submittingGate.value = false;
  }
}

onMounted(async () => {
  const sessionId = researcherStore.session?.id;
  if (sessionId === undefined) {
    return;
  }

  // Recover an interrupted flow from the server rather than trusting the
  // persisted store alone, the same reasoning as IntakePage.vue's own
  // onMounted: a submission can land server-side with its response never
  // arriving client-side.
  loading.value = true;
  try {
    intakeStore.hydrate(await getTechnologyIntake(sessionId));
    domainInput.value = intakeStore.domain;
    functionsInput.value = intakeStore.functions;
    formsInput.value = intakeStore.forms;
  } catch (error) {
    // A 404 is the ordinary "no intake yet" case, not surfaced -- the same
    // treatment IntakePage.vue gives getIntake's 404.
    if (!(error instanceof ApiError) || error.status !== 404) {
      errorMessage.value = describe(error);
    }
  } finally {
    loading.value = false;
  }
});
</script>
