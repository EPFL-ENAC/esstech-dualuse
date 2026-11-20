import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import type { ComprehensionResult, DiagnosticResult, IntakeState } from 'src/api/intake';
import { DIAGNOSTIC_ITEMS } from 'src/content/intake';

export type IntakeStep = 'diagnostic' | 'primer' | 'comprehension' | 'done';

/**
 * In-progress state for the intake.
 *
 * Each card submits first, then shows the outcome the backend returned, and
 * only `advance()` moves to the next card: receiving a result and leaving
 * the step are separate on purpose.
 *
 * Submitted answers can be read back from GET /sessions/{id}/intake, so what
 * needs persisting here is which step the learner is on and the answers they
 * have picked but not yet submitted.
 */
export const useIntakeStore = defineStore(
  'intake',
  () => {
    const step = ref<IntakeStep>('diagnostic');
    const diagnosticAnswers = ref<Record<string, string>>({});
    const diagnostic = ref<DiagnosticResult | null>(null);
    const comprehensionAnswer = ref<string | null>(null);
    const comprehension = ref<ComprehensionResult | null>(null);

    const diagnosticPassed = computed(() => {
      const result = diagnostic.value;
      return result !== null && result.diagnostic_score === result.correct_answers.length;
    });

    function setDiagnosticAnswer(itemId: string, value: string): void {
      diagnosticAnswers.value = { ...diagnosticAnswers.value, [itemId]: value };
    }

    function setDiagnostic(value: DiagnosticResult): void {
      diagnostic.value = value;
    }

    function setComprehensionAnswer(value: string): void {
      comprehensionAnswer.value = value;
    }

    function setComprehension(value: ComprehensionResult): void {
      comprehension.value = value;
    }

    /** Leave the current card, once its submission has a result. */
    function advance(): void {
      if (step.value === 'diagnostic' && diagnostic.value !== null) {
        // The backend records primer_shown for exactly those below the
        // threshold.
        step.value = diagnostic.value.above_threshold ? 'comprehension' : 'primer';
      } else if (step.value === 'primer') {
        step.value = 'comprehension';
      } else if (step.value === 'comprehension' && comprehension.value !== null) {
        step.value = 'done';
      }
    }

    /**
     * Rebuild the flow from stored server state after a reload.
     *
     * The persisted step is kept when the server state allows it, so a
     * submitted-but-not-advanced card resumes showing its outcome. Otherwise
     * the learner resumes on the card that shows the latest submission's
     * outcome: a finished-but-wrong intake lands on the comprehension card
     * with its correction, which they may never have seen before the reload.
     */
    function hydrate(state: IntakeState): void {
      diagnostic.value = {
        diagnostic_score: state.diagnostic_score,
        above_threshold: state.above_threshold,
        correct_answers: state.diagnostic_correct_answers,
      };
      // The API stores answers positionally: the nth answer belongs to the
      // nth item.
      const restored: Record<string, string> = {};
      DIAGNOSTIC_ITEMS.forEach((item, index) => {
        const answer = state.diagnostic_answers[index];
        if (answer !== undefined) {
          restored[item.id] = answer;
        }
      });
      diagnosticAnswers.value = restored;

      if (
        state.comprehension_answer === null ||
        state.comprehension_correct_answer === null ||
        state.scaffolding_depth === null
      ) {
        comprehension.value = null;
        if (step.value === 'done' || (step.value === 'primer' && !state.primer_shown)) {
          step.value = 'comprehension';
        }
        return;
      }

      comprehensionAnswer.value = state.comprehension_answer;
      comprehension.value = {
        correct: state.comprehension_correct === true,
        correct_answer: state.comprehension_correct_answer,
        scaffolding_depth: state.scaffolding_depth,
      };
      if (step.value !== 'done') {
        step.value = 'comprehension';
      }
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
      diagnosticPassed,
      setDiagnosticAnswer,
      setDiagnostic,
      setComprehensionAnswer,
      setComprehension,
      advance,
      hydrate,
      reset,
    };
  },
  { persist: true },
);
