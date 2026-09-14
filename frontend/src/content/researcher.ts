/**
 * Human-readable display labels for Domain, Function, and Form enum values.
 *
 * Function/Form/Domain taxonomy confirmed by the team (Louis). Display-layer
 * content only, mirroring content/patterns.ts's own split: API payloads use
 * the stable backend enum values, never these labels.
 *
 * Domain's own enum values are already the exact display strings (e.g.
 * "Cyber Technologies"), so there is no separate Domain label map -- the
 * value is the label. Function and Form are lowercase codes and do need one.
 */
import type { Domain, Form, Function } from 'src/api/researcher';

export interface FunctionOption {
  id: Function;
  label: string;
}

export interface FormOption {
  id: Form;
  label: string;
}

/**
 * `satisfies Record<Function, string>` makes a missing or misspelled id a
 * compile error rather than an undefined label at render time, the same
 * reason PATTERN_DISPLAY_BY_ID (content/patterns.ts) is written this way.
 */
export const FUNCTION_LABEL_BY_ID = {
  sensing: 'Sensing',
  generating: 'Generating',
  controlling: 'Controlling',
  predicting: 'Predicting',
  editing: 'Editing',
  optimizing: 'Optimizing',
  fabricating: 'Fabricating',
  computing: 'Computing',
} as const satisfies Record<Function, string>;

export const FORM_LABEL_BY_ID = {
  platform: 'Platform',
  model: 'Model',
  dataset: 'Dataset',
  protocol: 'Protocol',
  device: 'Device',
  infrastructure: 'Infrastructure',
  material: 'Material',
  method: 'Method',
} as const satisfies Record<Form, string>;

const FUNCTION_ORDER: readonly Function[] = [
  'sensing',
  'generating',
  'controlling',
  'predicting',
  'editing',
  'optimizing',
  'fabricating',
  'computing',
];

const FORM_ORDER: readonly Form[] = [
  'platform',
  'model',
  'dataset',
  'protocol',
  'device',
  'infrastructure',
  'material',
  'method',
];

export const FUNCTION_OPTIONS: readonly FunctionOption[] = FUNCTION_ORDER.map((id) => ({
  id,
  label: FUNCTION_LABEL_BY_ID[id],
}));

export const FORM_OPTIONS: readonly FormOption[] = FORM_ORDER.map((id) => ({
  id,
  label: FORM_LABEL_BY_ID[id],
}));

/**
 * Domain's enum values are already display strings, so this is just a
 * stated display order (the enum's own declaration order), matching how
 * content/patterns.ts states PATTERN_ORDER/GATE_ORDER explicitly rather
 * than relying on Object.entries() iteration order.
 */
export const DOMAIN_OPTIONS: readonly Domain[] = [
  'Material Science',
  'Advanced Manufacturing / 3D Printing',
  'Semiconductors and Nanotechnology',
  'Artificial Intelligence',
  'Cyber Technologies',
  'Quantum Technology',
  'Robotics & Autonomous Systems',
  'Neurotechnology',
  'Biochemistry',
];
