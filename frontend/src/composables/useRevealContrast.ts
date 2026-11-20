import { computed, ref } from 'vue';

import type { CounterCaseInfo, CounterCaseResponse } from 'src/api/contrast';
import type { ErrorState } from 'src/composables/useApiError';

export interface RevealContrastStore<Reveal, Contrast> {
  readonly reveal: Reveal | null;
  readonly counterCase: CounterCaseResponse | null;
  readonly contrast: Contrast | null;
  setReveal(value: Reveal): void;
  setCounterCase(value: CounterCaseResponse): void;
  setContrast(value: Contrast): void;
}

export interface RevealContrastApi<Reveal, Contrast> {
  reveal(id: string): Promise<Reveal>;
  getCounterCase(id: string): Promise<CounterCaseResponse>;
  submitContrast(id: string, learnerResponse: string | null): Promise<Contrast>;
}

/**
 * The post-commitment sequence both routes share: reveal, look up the
 * counter-case, then the contrast reflection. With no counter-case there is
 * nothing to reflect on, so the open-area acknowledgement (a null response)
 * is submitted on the learner's behalf.
 */
export function useRevealContrast<Reveal, Contrast>(options: {
  /** The encounter or session id; undefined while there is none. */
  targetId: () => string | undefined;
  store: RevealContrastStore<Reveal, Contrast>;
  api: RevealContrastApi<Reveal, Contrast>;
  errors: ErrorState;
}) {
  const { targetId, store, api, errors } = options;

  const revealing = ref(false);
  const loadingCounterCase = ref(false);
  const submittingContrast = ref(false);

  const twinCounterCase = computed<CounterCaseInfo | null>(() =>
    store.counterCase?.has_counter_case ? store.counterCase.counter_case : null,
  );

  // The counter-case lookup or the automatic open-area submission can fail,
  // or a reload can land between steps: the page then offers a manual retry.
  const counterCaseRetryNeeded = computed(
    () =>
      store.reveal !== null &&
      store.contrast === null &&
      twinCounterCase.value === null &&
      !loadingCounterCase.value &&
      !submittingContrast.value,
  );

  async function run(flag: { value: boolean }, step: (id: string) => Promise<void>) {
    const id = targetId();
    if (id === undefined) {
      return;
    }

    flag.value = true;
    errors.errorMessage.value = '';
    try {
      await step(id);
    } catch (error) {
      errors.report(error);
    } finally {
      flag.value = false;
    }
  }

  function submitContrast(learnerResponse: string | null): Promise<void> {
    return run(submittingContrast, async (id) => {
      store.setContrast(await api.submitContrast(id, learnerResponse));
    });
  }

  function requestCounterCase(): Promise<void> {
    return run(loadingCounterCase, async (id) => {
      const result = await api.getCounterCase(id);
      store.setCounterCase(result);
      if (!result.has_counter_case) {
        await submitContrast(null);
      }
    });
  }

  function requestReveal(): Promise<void> {
    return run(revealing, async (id) => {
      store.setReveal(await api.reveal(id));
      await requestCounterCase();
    });
  }

  return {
    revealing,
    submittingContrast,
    twinCounterCase,
    counterCaseRetryNeeded,
    requestReveal,
    requestCounterCase,
    submitContrast,
  };
}
