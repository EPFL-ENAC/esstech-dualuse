/**
 * Typed client for the intake endpoints.
 *
 * The answer key reaches the client only after submission: each result
 * carries the correct option ids for the items just submitted.
 */
import { apiFetch, postJson } from 'boot/api';

export const SCAFFOLDING_DEPTHS = ['high', 'standard', 'low'] as const;
export type ScaffoldingDepth = (typeof SCAFFOLDING_DEPTHS)[number];

export interface DiagnosticResult {
  diagnostic_score: number;
  above_threshold: boolean;
  /** The correct option id per diagnostic item, in item order. */
  correct_answers: string[];
}

export interface ComprehensionResult {
  correct: boolean;
  correct_answer: string;
  scaffolding_depth: ScaffoldingDepth;
}

export interface IntakeState {
  session_id: string;
  diagnostic_answers: string[];
  diagnostic_score: number;
  above_threshold: boolean;
  diagnostic_correct_answers: string[];
  primer_shown: boolean;
  created_at: string;
  comprehension_answer: string | null;
  comprehension_correct: boolean | null;
  /** Null until the comprehension answer is submitted. */
  comprehension_correct_answer: string | null;
  scaffolding_depth: ScaffoldingDepth | null;
  completed_at: string | null;
}

/**
 * Submit the three diagnostic answers, as option ids in item order.
 *
 * Safe to call repeatedly: the backend scores once and returns that same
 * result afterwards, so a retry is never a second submission.
 */
export function submitDiagnostic(sessionId: string, answers: string[]): Promise<DiagnosticResult> {
  return postJson<DiagnosticResult>(`/sessions/${sessionId}/intake/diagnostic`, {
    answers,
  });
}

/**
 * Submit the comprehension answer, finalizing the intake.
 *
 * This is one-shot by design: right or wrong, it stamps the scaffolding depth.
 * A wrong answer is followed by static correction content, never by a second
 * call here.
 */
export function submitComprehension(
  sessionId: string,
  answer: string,
): Promise<ComprehensionResult> {
  return postJson<ComprehensionResult>(`/sessions/${sessionId}/intake/comprehension`, {
    answer,
  });
}

/** Read the stored intake, so a reloaded page can resume mid-flow. */
export function getIntake(sessionId: string): Promise<IntakeState> {
  return apiFetch<IntakeState>(`/sessions/${sessionId}/intake`);
}
