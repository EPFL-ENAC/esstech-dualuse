/**
 * Typed client for the Student/Individual endpoints.
 *
 * The types below mirror the backend's response models exactly. Nothing here
 * carries a learner identifier: the backend derives the learner from its own
 * development cookie, which `apiFetch` forwards.
 */
import { apiFetch } from 'boot/api';

export const PATTERNS = [
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
] as const;
export type Pattern = (typeof PATTERNS)[number];

export const GATES = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6'] as const;
export type Gate = (typeof GATES)[number];

export type MatchResult = 'match' | 'partial_match' | 'mismatch';
export type CaseType = 'harm' | 'counter_case';
export type SessionRoute = 'student' | 'researcher';
export type SessionMode = 'individual' | 'group' | 'lecture';

export type FramingAnswers = Record<string, string>;

export interface SessionCreated {
  id: string;
  route: SessionRoute;
  mode: SessionMode;
  started_at: string;
}

/** A case before commitment. Carries no answer-key fields by construction. */
export interface CaseCandidate {
  id: string;
  title: string;
  area: string;
  case_type: CaseType;
  narrative_until_crossroads: string;
}

export interface EncounterCreated {
  id: string;
  session_id: string;
  sequence_no: number;
  created_at: string;
  case: CaseCandidate;
}

export interface CommitmentCreated {
  id: string;
  case_encounter_id: string;
  sequence_no: number;
  pattern: Pattern;
  gate: Gate;
  framing_answers: FramingAnswers;
  created_at: string;
}

export interface RevealedCommitment {
  pattern: Pattern;
  gate: Gate;
}

/** The case with its answer key. Only ever present in a reveal response. */
export interface RevealedCase {
  id: string;
  title: string;
  full_narrative: string;
  main_path_pattern: Pattern;
  main_path_gate: Gate;
  source_references: string[];
}

export interface RevealResponse {
  feedback_record_id: string;
  match_result: MatchResult;
  revealed_at: string;
  commitment: RevealedCommitment;
  case: RevealedCase;
}

export type ContrastType = 'twin_counter_case' | 'open_area';

/** The counter-case fields shown before the WHO reflection question. */
export interface CounterCaseInfo {
  counter_case_id: string;
  gate_lever: Gate;
  responsibility_posture_contrast: string;
}

export interface CounterCaseResponse {
  has_counter_case: boolean;
  counter_case: CounterCaseInfo | null;
}

export interface ContrastResponse {
  contrast_entry_id: string;
  contrast_type: ContrastType;
  counter_case_id: string | null;
  learner_response: string | null;
  created_at: string;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function createSession(): Promise<SessionCreated> {
  return apiFetch<SessionCreated>('/sessions', { method: 'POST' });
}

export function listCandidateCases(): Promise<CaseCandidate[]> {
  return apiFetch<CaseCandidate[]>('/cases/candidates');
}

export function createEncounter(sessionId: string, caseId: string): Promise<EncounterCreated> {
  return postJson<EncounterCreated>(`/sessions/${sessionId}/encounters`, { case_id: caseId });
}

export function createCommitment(
  encounterId: string,
  payload: { pattern: Pattern; gate: Gate; framing_answers: FramingAnswers },
): Promise<CommitmentCreated> {
  return postJson<CommitmentCreated>(`/encounters/${encounterId}/commitments`, payload);
}

/**
 * Ask for the encounter's reveal.
 *
 * Safe to call repeatedly: the backend computes the verdict once and returns
 * that same record afterwards, so a retry is never a second submission.
 */
export function revealEncounter(encounterId: string): Promise<RevealResponse> {
  return apiFetch<RevealResponse>(`/encounters/${encounterId}/reveal`, { method: 'POST' });
}

/**
 * Look up the encounter's counter-case, if any.
 *
 * Never a 404 for "no counter-case" -- that's a valid corpus state reported
 * as `has_counter_case: false`, not an error.
 */
export function getCounterCase(encounterId: string): Promise<CounterCaseResponse> {
  return apiFetch<CounterCaseResponse>(`/encounters/${encounterId}/counter-case`);
}

/**
 * Submit the post-reveal contrast reflection.
 *
 * Safe to call repeatedly, the same way revealEncounter is: the backend
 * derives contrast_type itself and returns the stored entry afterwards.
 */
export function submitContrast(
  encounterId: string,
  learnerResponse: string | null,
): Promise<ContrastResponse> {
  return postJson<ContrastResponse>(`/encounters/${encounterId}/contrast`, {
    learner_response: learnerResponse,
  });
}
