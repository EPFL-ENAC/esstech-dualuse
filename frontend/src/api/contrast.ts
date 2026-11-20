/**
 * Counter-case types shared by both routes: the student encounter endpoint
 * and the researcher comparison-set endpoint return the same schema.
 */
import type { Gate } from 'src/api/taxonomy';

/** The counter-case fields shown before the reflection question. */
export interface CounterCaseInfo {
  counter_case_id: string;
  gate_lever: Gate;
  responsibility_posture_contrast: string;
}

/**
 * "No counter-case" is a valid corpus state, reported as
 * `has_counter_case: false`, never a 404.
 */
export interface CounterCaseResponse {
  has_counter_case: boolean;
  counter_case: CounterCaseInfo | null;
}
