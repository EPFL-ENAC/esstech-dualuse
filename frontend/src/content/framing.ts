/**
 * Temporary framing prompts shown before a learner commits.
 *
 * These are placeholder wording pending the real question set, and they live
 * here rather than in i18n because `key` is written verbatim into the
 * commitment's `framing_answers` JSON and must stay stable across locales.
 */

export type FramingQuestionKind = 'text' | 'gate';

export interface FramingQuestion {
  /** Stored as-is in framing_answers. Never translate or rename casually. */
  key: string;
  prompt: string;
  kind: FramingQuestionKind;
}

export const FRAMING_QUESTIONS: readonly FramingQuestion[] = [
  {
    key: 'decision_owner',
    prompt: 'Who is making the decision at this point?',
    kind: 'text',
  },
  {
    key: 'capability',
    prompt: 'What capability is being developed or released?',
    kind: 'text',
  },
  {
    key: 'repurposing',
    prompt: 'Who else could repurpose this capability, and for what purpose?',
    kind: 'text',
  },
  {
    // The learner's own reading of where this sits. Deliberately separate from
    // the commitment's top-level gate: the two may coincide, but one is never
    // derived from the other.
    key: 'gate',
    prompt: 'At which decision gate does this choice occur?',
    kind: 'gate',
  },
];
