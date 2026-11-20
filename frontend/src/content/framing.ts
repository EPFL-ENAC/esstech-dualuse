/**
 * Temporary framing prompts shown before a learner commits.
 *
 * These are placeholder wording pending the real question set, and they live
 * here rather than in i18n because `key` is written verbatim into the
 * commitment's `framing_answers` JSON and must stay stable across locales.
 */

export interface FramingQuestion {
  /** Stored as-is in framing_answers. Never translate or rename casually. */
  key: string;
  prompt: string;
}

export const FRAMING_QUESTIONS: readonly FramingQuestion[] = [
  {
    key: 'decision_owner',
    prompt: 'Who is making the decision at this point?',
  },
  {
    key: 'capability',
    prompt: 'What capability is being developed or released?',
  },
  {
    key: 'repurposing',
    prompt: 'Who else could repurpose this capability, and for what purpose?',
  },
];
