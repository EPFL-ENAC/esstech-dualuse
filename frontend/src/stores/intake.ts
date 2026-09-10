import { defineStore } from 'pinia';
import { ref } from 'vue';

import type { ComprehensionResult, DiagnosticResult, IntakeState } from 'src/api/intake';
import { DIAGNOSTIC_ITEMS } from 'src/content/intake';

export type IntakeStep = 'diagnostic' | 'primer' | 'comprehension' | 'correction' | 'done';

/**
 * In-progress state for the M0 intake.
 *
 * A sibling of the student store rather than part of it. `student.ts` exists
 * because the API offers no way to read a session or encounter back; intake
 * does have GET /sessions/{id}/intake, so what needs persisting here is
 * different -- which step the learner is on, and the answers they have picked
 * but not yet submitted. Keeping it separate also keeps M0 deletable in one
 * piece.
 *
 * The session itself deliberately lives in the student store, not here: the
 * flow hands off to the Student/Individual path when it finishes, and that
 * path reads the session from there.
 */
export const useIntakeStore = defineStore(
  'intake',
  () => {
    const step = ref<IntakeStep>('diagnostic');
    // Keyed by item id rather than positional, so a half-finished diagnostic
    // survives a reload without depending on option order.
    const diagnosticAnswers = ref<Record<string, string>>({});
    const diagnostic = ref<DiagnosticResult | null>(null);
    const comprehensionAnswer = ref<string | null>(null);
    const comprehension = ref<ComprehensionResult | null>(null);

    function setStep(value: IntakeStep): void {
      step.value = value;
    }

    function setDiagnosticAnswer(itemId: string, value: string): void {
      diagnosticAnswers.value = { ...diagnosticAnswers.value, [itemId]: value };
    }

    function setDiagnostic(value: DiagnosticResult): void {
      diagnostic.value = value;
      // The primer is shown to exactly those below the threshold, matching
      // what the backend recorded as primer_shown.
      step.value = value.above_threshold ? 'comprehension' : 'primer';
    }

    function setComprehension(value: ComprehensionResult): void {
      comprehension.value = value;
      step.value = value.correct ? 'done' : 'correction';
    }

    /** Rebuild the flow from stored server state after a reload. */
    function hydrate(state: IntakeState): void {
      diagnostic.value = {
        diagnostic_score: state.diagnostic_score,
        above_threshold: state.above_threshold,
      };
      // Positional, matching the API contract: the nth stored answer belongs
      // to the nth item. The ids come from DIAGNOSTIC_ITEMS rather than from a
      // template string, because the placeholder ids are documented as
      // temporary -- guessing `d${n}` would silently rebuild the answers under
      // keys the radio groups no longer look up the moment real items land,
      // leaving a resumed flow looking blank with the answers already stored.
      const restored: Record<string, string> = {};
      DIAGNOSTIC_ITEMS.forEach((item, index) => {
        const answer = state.diagnostic_answers[index];
        if (answer !== undefined) {
          restored[item.id] = answer;
        }
      });
      diagnosticAnswers.value = restored;
      comprehensionAnswer.value = state.comprehension_answer;

      if (state.completed_at === null || state.scaffolding_depth === null) {
        step.value = state.primer_shown ? 'primer' : 'comprehension';
        return;
      }

      comprehension.value = {
        correct: state.comprehension_correct === true,
        scaffolding_depth: state.scaffolding_depth,
      };
      // A finished-but-wrong intake resumes on the correction, not on 'done':
      // the learner may never have seen it before the reload.
      step.value = state.comprehension_correct === true ? 'done' : 'correction';
    }

    function reset(): void {
      step.value = 'diagnostic';
      diagnosticAnswers.value = {};
      diagnostic.value = null;
      comprehensionAnswer.value = null;
      comprehension.value = null;
    }

    return {
      step,
      diagnosticAnswers,
      diagnostic,
      comprehensionAnswer,
      comprehension,
      setStep,
      setDiagnosticAnswer,
      setDiagnostic,
      setComprehension,
      hydrate,
      reset,
    };
  },
  { persist: true },
);
