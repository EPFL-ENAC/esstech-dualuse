import { defineStore } from 'pinia';
import { ref } from 'vue';

import type { CounterCaseResponse } from 'src/api/contrast';
import type {
  ComparisonSetResult,
  PredictionSubmissionResult,
  RevealComparison,
  SetContrastResponse,
} from 'src/api/researcher';
import type { SessionCreated } from 'src/api/sessions';
import { useResearcherIntakeStore } from 'stores/researcherIntake';

export const useResearcherStore = defineStore(
  'researcher',
  () => {
    const session = ref<SessionCreated | null>(null);
    const comparisonSet = ref<ComparisonSetResult | null>(null);
    const prediction = ref<PredictionSubmissionResult | null>(null);
    const reveal = ref<RevealComparison | null>(null);
    const counterCase = ref<CounterCaseResponse | null>(null);
    const contrast = ref<SetContrastResponse | null>(null);

    /** A new session starts the whole route afresh, intake included. */
    function setSession(value: SessionCreated): void {
      startOver();
      session.value = value;
    }

    function setComparisonSet(value: ComparisonSetResult): void {
      clearComparisonSet();
      comparisonSet.value = value;
    }

    function setPrediction(value: PredictionSubmissionResult): void {
      prediction.value = value;
    }

    function setReveal(value: RevealComparison): void {
      reveal.value = value;
    }

    function setCounterCase(value: CounterCaseResponse): void {
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

    /** Abandon the whole Researcher route, intake included, to begin again. */
    function startOver(): void {
      session.value = null;
      clearComparisonSet();
      useResearcherIntakeStore().reset();
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
      startOver,
    };
  },
  { persist: true },
);
