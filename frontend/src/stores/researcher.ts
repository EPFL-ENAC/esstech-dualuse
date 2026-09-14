import { defineStore } from 'pinia';
import { ref } from 'vue';

import type {
  ComparisonSetResult,
  PredictionSubmissionResult,
  RevealComparison,
  SetContrastResponse,
  SetCounterCaseResponse,
} from 'src/api/researcher';
import type { SessionCreated } from 'src/api/sessions';

/**
 * Flow state for the Researcher/Individual path.
 *
 * A sibling of the student store, not part of it -- a Researcher-route
 * session has no business living in a store documented as Student-only.
 *
 * comparisonSet/prediction/reveal/counterCase/contrast mirror
 * useStudentStore's own encounter/commitment/reveal/counterCase/contrast
 * shape exactly: this is Blocco 6, the Researcher route's equivalent of
 * Student's ongoing work loop (not a one-time setup phase, which is why
 * it lives here rather than in its own store the way researcherIntake.ts
 * does for the intake/tag/gate setup phase).
 */
export const useResearcherStore = defineStore(
  'researcher',
  () => {
    const session = ref<SessionCreated | null>(null);
    const comparisonSet = ref<ComparisonSetResult | null>(null);
    const prediction = ref<PredictionSubmissionResult | null>(null);
    const reveal = ref<RevealComparison | null>(null);
    const counterCase = ref<SetCounterCaseResponse | null>(null);
    const contrast = ref<SetContrastResponse | null>(null);

    function setSession(value: SessionCreated): void {
      session.value = value;
      clearComparisonSet();
    }

    function setComparisonSet(value: ComparisonSetResult): void {
      comparisonSet.value = value;
      prediction.value = null;
      reveal.value = null;
      counterCase.value = null;
      contrast.value = null;
    }

    function setPrediction(value: PredictionSubmissionResult): void {
      prediction.value = value;
    }

    function setReveal(value: RevealComparison): void {
      reveal.value = value;
    }

    function setCounterCase(value: SetCounterCaseResponse): void {
      counterCase.value = value;
    }

    function setContrast(value: SetContrastResponse): void {
      contrast.value = value;
    }

    function clearComparisonSet(): void {
      comparisonSet.value = null;
      prediction.value = null;
      reveal.value = null;
      counterCase.value = null;
      contrast.value = null;
    }

    function reset(): void {
      session.value = null;
      clearComparisonSet();
    }

    return {
      session,
      comparisonSet,
      prediction,
      reveal,
      counterCase,
      contrast,
      setSession,
      setComparisonSet,
      setPrediction,
      setReveal,
      setCounterCase,
      setContrast,
      clearComparisonSet,
      reset,
    };
  },
  { persist: true },
);
