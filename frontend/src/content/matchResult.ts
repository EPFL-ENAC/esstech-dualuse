import type { MatchResult } from 'src/api/student';
import type { MessageKey } from 'src/i18n';

export interface MatchResultDisplay {
  /** A Quasar brand colour name, used as `bg-${color}`. */
  color: string;
  labelKey: MessageKey;
  hintKey: MessageKey;
  /** Takes {pattern} and {gate}: the learner's committed reading. */
  reflectionKey: MessageKey;
}

export const MATCH_RESULT_DISPLAY = {
  match: {
    color: 'positive',
    labelKey: 'matchMatch',
    hintKey: 'matchMatchHint',
    reflectionKey: 'reflectionMatch',
  },
  partial_match: {
    color: 'warning',
    labelKey: 'matchPartial',
    hintKey: 'matchPartialHint',
    reflectionKey: 'reflectionPartialMatch',
  },
  mismatch: {
    color: 'negative',
    labelKey: 'matchMismatch',
    hintKey: 'matchMismatchHint',
    reflectionKey: 'reflectionMismatch',
  },
} as const satisfies Record<MatchResult, MatchResultDisplay>;
