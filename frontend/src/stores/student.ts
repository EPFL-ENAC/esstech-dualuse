import { defineStore } from 'pinia';
import { ref } from 'vue';

import type {
  CommitmentCreated,
  EncounterCreated,
  RevealResponse,
  SessionCreated,
} from 'src/api/student';

/**
 * Flow state for the Student/Individual path.
 *
 * Persisted because the API exposes no way to read a session or encounter back:
 * every endpoint creates something. Without this, a page reload would strand
 * the learner mid-flow, and re-selecting the same case is rejected as a
 * duplicate.
 */
export const useStudentStore = defineStore(
  'student',
  () => {
    const session = ref<SessionCreated | null>(null);
    const encounter = ref<EncounterCreated | null>(null);
    const commitment = ref<CommitmentCreated | null>(null);
    const reveal = ref<RevealResponse | null>(null);

    function setSession(value: SessionCreated): void {
      session.value = value;
      clearEncounter();
    }

    function setEncounter(value: EncounterCreated): void {
      encounter.value = value;
      commitment.value = null;
      reveal.value = null;
    }

    function setCommitment(value: CommitmentCreated): void {
      commitment.value = value;
    }

    function setReveal(value: RevealResponse): void {
      reveal.value = value;
    }

    function clearEncounter(): void {
      encounter.value = null;
      commitment.value = null;
      reveal.value = null;
    }

    function reset(): void {
      session.value = null;
      clearEncounter();
    }

    return {
      session,
      encounter,
      commitment,
      reveal,
      setSession,
      setEncounter,
      setCommitment,
      setReveal,
      clearEncounter,
      reset,
    };
  },
  { persist: true },
);
