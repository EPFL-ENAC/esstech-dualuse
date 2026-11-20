import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import type {
  GateAndPostureResult,
  MappingStatus,
  TagResult,
  TechnologyIntakeCreated,
  TechnologyIntakeState,
} from 'src/api/researcher';
import type { Domain, Form, Function, Gate } from 'src/api/taxonomy';

export type ResearcherIntakeStep =
  'description' | 'tagging' | 'exhausted' | 'gate-and-posture' | 'done';

/** In-progress state for the Researcher intake -> tag -> gate-and-posture flow. */
export const useResearcherIntakeStore = defineStore(
  'researcherIntake',
  () => {
    const step = ref<ResearcherIntakeStep>('description');
    const rawDescription = ref<string | null>(null);
    const domain = ref<Domain | null>(null);
    const functions = ref<Function[]>([]);
    const forms = ref<Form[]>([]);
    const mappingStatus = ref<MappingStatus | null>(null);
    const attemptsUsed = ref(0);
    const attemptsRemaining = ref<number | null>(null);
    const gate = ref<Gate | null>(null);
    const postureResponse = ref<string | null>(null);

    const hasAttemptedTag = computed(() => attemptsUsed.value > 0);

    function setStep(value: ResearcherIntakeStep): void {
      step.value = value;
    }

    function setIntakeCreated(value: TechnologyIntakeCreated): void {
      rawDescription.value = value.raw_description;
      mappingStatus.value = value.mapping_status;
      step.value = 'tagging';
    }

    function setTagResult(value: TagResult): void {
      domain.value = value.domain;
      functions.value = value.functions;
      forms.value = value.forms;
      mappingStatus.value = value.mapping_status;
      attemptsUsed.value = value.attempts_used;
      attemptsRemaining.value = value.attempts_remaining;
      if (value.mapping_status !== 'mapped' && value.attempts_remaining === 0) {
        step.value = 'exhausted';
      }
    }

    function setGateAndPosture(value: GateAndPostureResult): void {
      gate.value = value.gate;
      postureResponse.value = value.posture_response;
      step.value = 'done';
    }

    /** Rebuild the flow from stored server state after a reload. */
    function hydrate(state: TechnologyIntakeState): void {
      rawDescription.value = state.raw_description;
      domain.value = state.domain;
      functions.value = state.functions;
      forms.value = state.forms;
      mappingStatus.value = state.mapping_status;
      attemptsUsed.value = state.attempts_used;
      attemptsRemaining.value = state.attempts_remaining;
      gate.value = state.gate;
      postureResponse.value = state.posture_response;

      if (state.gate !== null) {
        step.value = 'done';
      } else if (state.mapping_status === 'mapped') {
        step.value = 'gate-and-posture';
      } else if (state.attempts_remaining === 0) {
        step.value = 'exhausted';
      } else {
        step.value = 'tagging';
      }
    }

    function reset(): void {
      step.value = 'description';
      rawDescription.value = null;
      domain.value = null;
      functions.value = [];
      forms.value = [];
      mappingStatus.value = null;
      attemptsUsed.value = 0;
      attemptsRemaining.value = null;
      gate.value = null;
      postureResponse.value = null;
    }

    return {
      step,
      rawDescription,
      domain,
      functions,
      forms,
      mappingStatus,
      attemptsUsed,
      attemptsRemaining,
      hasAttemptedTag,
      gate,
      postureResponse,
      setStep,
      setIntakeCreated,
      setTagResult,
      setGateAndPosture,
      hydrate,
      reset,
    };
  },
  { persist: true },
);
