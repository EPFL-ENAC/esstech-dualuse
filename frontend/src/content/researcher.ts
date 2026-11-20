import { DOMAINS, FORMS, FUNCTIONS } from 'src/api/taxonomy';
import type { Domain, Form, Function } from 'src/api/taxonomy';
/**
 * Human-readable display labels for Domain, Function, and Form enum values.
 *
 * Taxonomy confirmed by the team (Louis). Display-layer content only: API
 * payloads use the stable backend enum values, never these labels. Domain's
 * backend values are already display strings, so it needs no label map.
 */

/** A ready-to-use q-select option (emit-value, map-options). */
export interface SelectOption<T extends string> {
  value: T;
  label: string;
}

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

export const DOMAIN_OPTIONS: readonly SelectOption<Domain>[] = DOMAINS.map((value) => ({
  value,
  label: value,
}));

export const FUNCTION_OPTIONS: readonly SelectOption<Function>[] = FUNCTIONS.map((value) => ({
  value,
  label: FUNCTION_LABEL_BY_ID[value],
}));

export const FORM_OPTIONS: readonly SelectOption<Form>[] = FORMS.map((value) => ({
  value,
  label: FORM_LABEL_BY_ID[value],
}));
