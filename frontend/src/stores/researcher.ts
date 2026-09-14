import { defineStore } from 'pinia';
import { ref } from 'vue';

import type { SessionCreated } from 'src/api/sessions';

/**
 * Flow state for the Researcher/Individual path.
 *
 * A sibling of the student store, not part of it -- a Researcher-route
 * session has no business living in a store documented as Student-only.
 * Minimal for now: RouteChoicePage.vue only needs to persist the session it
 * just created. Expanded when Blocco 5 (the real Researcher intake/tag/
 * gate/comparison flow) is built, the same way the student store grew encounter
 * by encounter rather than being fully speculated up front.
 */
export const useResearcherStore = defineStore(
  'researcher',
  () => {
    const session = ref<SessionCreated | null>(null);

    function setSession(value: SessionCreated): void {
      session.value = value;
    }

    function reset(): void {
      session.value = null;
    }

    return {
      session,
      setSession,
      reset,
    };
  },
  { persist: true },
);
