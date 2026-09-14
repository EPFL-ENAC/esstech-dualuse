import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import type {
  Domain,
  Form,
  Function,
  GateAndPostureResult,
  MappingStatus,
  TagResult,
  TechnologyIntakeCreated,
  TechnologyIntakeState,
} from 'src/api/researcher';
import type { Gate } from 'src/api/student';

export type ResearcherIntakeStep =
  'description' | 'tagging' | 'exhausted' | 'gate-and-posture' | 'done';

/**
 * In-progress state for the Researcher intake -> tag -> gate-and-posture
 * flow, the Researcher-route counterpart of stores/intake.ts.
 *
 * A sibling of the researcher store (which only holds the session), the
 * same reason intake.ts is a sibling of the student store rather than part
 * of it: this needs a step field and the accumulated intake facets, a
 * different shape from "the session, once created."
 */
export const useResearcherIntakeStore = defineStore(
  'researcherIntake',
  () => {
    const step = ref<ResearcherIntakeStep>('description');
    const rawDescription = ref<string | null>(null);
    const domain = ref<Domain | null>(null);
    const functions = ref<Function[]>([]);
    const forms = ref<Form[]>([]);
    const mappingStatus = ref<MappingStatus | null>(null);
    const attemptsRemaining = ref<number | null>(null);
    const gate = ref<Gate | null>(null);
    const postureResponse = ref<string | null>(null);

    // Whether at least one /tag attempt has been submitted. Derived, not
    // stored: within the 'tagging' step, attemptsRemaining only ever takes
    // 2 (the untouched MAX_TAG_ATTEMPTS budget, backend api/services/
    // researcher.py) or 1 (one attempt spent) -- 0 always means MAPPED or
    // 'exhausted', neither of which renders this. attemptsRemaining < 2
    // already distinguishes "never attempted" from "attempted once" on its
    // own, so this needs no separate field to track alongside it.
    const hasAttemptedTag = computed(
      () => attemptsRemaining.value !== null && attemptsRemaining.value < 2,
    );

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
      attemptsRemaining.value = value.attempts_remaining;
      // Reaching MAPPED or exhausting the budget both stop the tag loop;
      // MAPPED still requires an explicit "Continue" click (rendered
      // inside the 'tagging' step itself, based on mappingStatus) before
      // moving on, the same way M0 never auto-advances a step either.
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
