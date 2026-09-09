/**
 * Human-readable display labels for Pattern and Gate enum values.
 *
 * Source: CURRENTCROSS — Recurring Pattern Findings, version 5,
 * 5 June 2026.
 *
 * Provisional pending author review. Update names and descriptions if
 * the source document is revised.
 *
 * Display-layer content only. API payloads must continue to use the
 * stable backend enum IDs: Pattern A–P and Gate G1–G6.
 */
import type { Gate, Pattern } from 'src/api/student';

export interface PatternDisplay {
  label: string;
  description: string;
}

export interface GateDisplay {
  label: string;
}

export interface PatternOption extends PatternDisplay {
  id: Pattern;
}

export interface GateOption extends GateDisplay {
  id: Gate;
}

/**
 * Keyed by enum ID so a reveal or a stored commitment can look its display text
 * up directly. `satisfies Record<Pattern, …>` makes a missing or misspelled ID a
 * compile error rather than an `undefined` label at render time.
 */
export const PATTERN_DISPLAY_BY_ID = {
  A: {
    label: 'A — transferability',
    description:
      'A general-purpose capability moves easily into targeting, surveillance, or coercion.',
  },
  B: {
    label: 'B — funder-framing',
    description:
      'Who pays steers the direction of the work, and the likely uses are foreseeable from the start.',
  },
  C: {
    label: 'C — democratisation',
    description:
      'Making something cheaper or easier for legitimate users makes it easier for bad actors too.',
  },
  D: {
    label: 'D — diagnostic-disclosure',
    description:
      'Defensive or diagnostic research reveals a weakness; responsible-disclosure norms apply.',
  },
  E: {
    label: 'E — identity-inference',
    description:
      'Inferring or classifying personal traits, with the downside falling hardest on specific groups.',
  },
  F: {
    label: 'F — anticipatory-governance',
    description:
      'Planning ahead to prevent harm — staged release, designing risk out, coalitions, treaties.',
  },
  G: {
    label: 'G — downstream-control',
    description:
      'How access is designed (open weights vs. an API, terms of use, screening) decides how controllable it stays.',
  },
  H: {
    label: 'H — direct-lethality',
    description:
      'A short, direct path from the result to physical injury or a life-critical failure.',
  },
  I: {
    label: 'I — incentive-misalignment',
    description:
      'The thing being rewarded (profit, grants, publications, prestige) diverges from what is good for society.',
  },
  J: {
    label: 'J — norm-deviation',
    description:
      'Going ahead despite explicit warnings from peers, ethics bodies, or affected communities.',
  },
  K: {
    label: 'K — strategic-destabilisation',
    description:
      'Shifts the long-term balance of security or deterrence over a 10–30 year horizon.',
  },
  L: {
    label: 'L — chokepoint',
    description: 'Success creates a single point of failure or leverage at strategic scale.',
  },
  M: {
    label: 'M — path-dependency',
    description:
      'Built-up momentum, funding, or commitment makes a risky direction hard to reverse.',
  },
  N: {
    label: 'N — responsibility-diffusion',
    description: 'The downstream risk falls between the cracks — no one team owns it.',
  },
  O: {
    label: 'O — consent-bypass',
    description:
      'The work is built on data taken from people without meaningful consent, then reused.',
  },
  P: {
    label: 'P — community-mobilisation',
    description:
      'Collective pushback against a specific project — open letters, boycotts, retractions, refusals.',
  },
} as const satisfies Record<Pattern, PatternDisplay>;

export const GATE_DISPLAY_BY_ID = {
  G1: {
    label: 'G1 — Choosing the problem',
  },
  G2: {
    label: 'G2 — Accepting funding / partnership',
  },
  G3: {
    label: 'G3 — Designing the method and data',
  },
  G4: {
    label: 'G4 — Publishing / disclosure',
  },
  G5: {
    label: 'G5 — Deciding how to release it',
  },
  G6: {
    label: 'G6 — Deployment and downstream use',
  },
} as const satisfies Record<Gate, GateDisplay>;

/**
 * Display order for the pickers, stated explicitly rather than derived from the
 * records above.
 *
 * The source document groups patterns by layer (harm mechanisms / conditions and
 * levers / responses), not alphabetically. If PATTERN_DISPLAY_BY_ID is ever
 * reordered to mirror that grouping, `Object.entries()` would silently reorder
 * the picker with it; this array keeps A→P a stated fact, independent of how the
 * record happens to be written.
 */
const PATTERN_ORDER: readonly Pattern[] = [
  'A',
  'B',
  'C',
  'D',
  'E',
  'F',
  'G',
  'H',
  'I',
  'J',
  'K',
  'L',
  'M',
  'N',
  'O',
  'P',
];

const GATE_ORDER: readonly Gate[] = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6'];

export const PATTERN_OPTIONS: readonly PatternOption[] = PATTERN_ORDER.map((id) => ({
  id,
  ...PATTERN_DISPLAY_BY_ID[id],
}));

export const GATE_OPTIONS: readonly GateOption[] = GATE_ORDER.map((id) => ({
  id,
  ...GATE_DISPLAY_BY_ID[id],
}));
