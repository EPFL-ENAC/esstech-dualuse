/** Typed client for the Researcher/Individual endpoints. */
import { apiFetch, postJson } from 'boot/api';
import type { CounterCaseResponse } from 'src/api/contrast';
import type { ContrastType, Domain, Form, Function, Gate, Pattern } from 'src/api/taxonomy';

export type MappingStatus = 'unmapped' | 'partial' | 'mapped';

export interface TechnologyIntakeCreated {
  id: string;
  session_id: string;
  raw_description: string;
  mapping_status: MappingStatus;
  created_at: string;
}

/** The full stored technology intake, for recovering an interrupted flow. */
export interface TechnologyIntakeState {
  session_id: string;
  raw_description: string;
  domain: Domain | null;
  functions: Function[];
  forms: Form[];
  mapping_status: MappingStatus;
  attempts_used: number;
  attempts_remaining: number;
  gate: Gate | null;
  posture_response: string | null;
  created_at: string;
}

export interface TagResult {
  domain: Domain | null;
  functions: Function[];
  forms: Form[];
  mapping_status: MappingStatus;
  attempts_used: number;
  attempts_remaining: number;
}

export interface GateAndPostureResult {
  gate: Gate;
  posture_response: string;
}

export type InclusionReason = 'shared_function' | 'widened_by_domain';

/** One case in a comparison set, in relevance order. */
export interface ComparisonSetCaseSummary {
  case_id: string;
  title: string;
  domain: Domain;
}

/** The cases matched to a session's technology intake. */
export interface ComparisonSetResult {
  cases: ComparisonSetCaseSummary[];
  was_widened: boolean;
  case_count: number;
}

export interface PredictionEntry {
  rank: number;
  pattern: Pattern;
}

export interface PredictionSubmissionResult {
  predictions: PredictionEntry[];
}

/**
 * A session's prediction compared against its comparison set's tagged
 * pattern distribution: structured facts, not a verdict.
 */
export interface RevealComparison {
  dominant_pattern: Pattern | null;
  secondary_patterns: Pattern[];
  predictions: PredictionEntry[];
  top_prediction_is_dominant: boolean;
  predictions_in_secondary: Pattern[];
  predictions_not_activated: Pattern[];
}

/** The stored set-level contrast entry, whichever branch produced it. */
export interface SetContrastResponse {
  set_contrast_entry_id: string;
  contrast_type: ContrastType;
  learner_response: string | null;
  created_at: string;
}

export type TraceCompleteness = 'full' | 'boundary_exit' | 'zero_pattern' | 'in_progress';

/**
 * The Researcher-route debrief.
 *
 * Every optional field is absent, not null, until trace_completeness reaches
 * the point where it is meaningful: absent means "not reached yet", never
 * "empty result". A present list can still be empty (e.g. secondary_patterns
 * in a "full" report where nothing secondary activated).
 */
export interface ResearcherSessionReport {
  trace_completeness: TraceCompleteness;
  domain?: Domain;
  functions?: Function[];
  forms?: Form[];
  gate?: Gate;
  posture_response?: string;
  case_count?: number;
  was_widened?: boolean;
  predictions?: PredictionEntry[];
  dominant_pattern?: Pattern;
  secondary_patterns?: Pattern[];
  top_prediction_is_dominant?: boolean;
  contrast_type?: ContrastType;
  learner_response?: string;
  gate_lever?: Gate;
}

/**
 * One case from a session's comparison set, with why it was included.
 *
 * full_narrative, main_path_pattern, main_path_gate and source_references
 * are the answer key: absent (not null) until the session has a submitted
 * prediction.
 */
export interface ResearcherCaseDetail {
  case_id: string;
  title: string;
  area: string;
  narrative_until_crossroads: string;
  domain: Domain;
  functions: Function[];
  forms: Form[];
  inclusion_reason: InclusionReason;
  full_narrative?: string;
  main_path_pattern?: Pattern;
  main_path_gate?: Gate;
  source_references?: string[];
}

/**
 * Start the session's technology intake from its free-text description.
 * One-shot: a second call for a session that already has an intake is
 * rejected.
 */
export function createTechnologyIntake(
  sessionId: string,
  rawDescription: string,
): Promise<TechnologyIntakeCreated> {
  return postJson<TechnologyIntakeCreated>(`/sessions/${sessionId}/researcher/intake`, {
    raw_description: rawDescription,
  });
}

/**
 * Read the session's stored technology intake, so a reloaded page can
 * resume mid-flow. A 404 means "not started yet", not an error.
 */
export function getTechnologyIntake(sessionId: string): Promise<TechnologyIntakeState> {
  return apiFetch<TechnologyIntakeState>(`/sessions/${sessionId}/researcher/intake`);
}

/**
 * Submit one /tag attempt. The backend allows two in total and reports what
 * is left in attempts_remaining.
 */
export function submitTag(
  sessionId: string,
  payload: { domain: Domain | null; functions: Function[]; forms: Form[] },
): Promise<TagResult> {
  return postJson<TagResult>(`/sessions/${sessionId}/researcher/tag`, payload);
}

/**
 * Submit the decision gate and responsibility posture. Only meaningful once
 * the technology mapping is complete, and one-shot once submitted.
 */
export function setGateAndPosture(
  sessionId: string,
  payload: { gate: Gate; posture_response: string },
): Promise<GateAndPostureResult> {
  return postJson<GateAndPostureResult>(
    `/sessions/${sessionId}/researcher/gate-and-posture`,
    payload,
  );
}

/**
 * Match the session's technology intake against the case corpus.
 * Idempotent: computed once, then returned unchanged on every later call.
 */
export function buildComparisonSet(sessionId: string): Promise<ComparisonSetResult> {
  return apiFetch<ComparisonSetResult>(`/sessions/${sessionId}/researcher/comparison-set`, {
    method: 'POST',
  });
}

/**
 * Submit the session's one-shot ranked pattern prediction (2 or 3 entries).
 * A second submission for the same session is rejected.
 */
export function submitPrediction(
  sessionId: string,
  predictions: PredictionEntry[],
): Promise<PredictionSubmissionResult> {
  return postJson<PredictionSubmissionResult>(`/sessions/${sessionId}/researcher/prediction`, {
    predictions,
  });
}

/**
 * Compare the session's submitted prediction against its comparison set's
 * tagged-pattern distribution. Recomputed on every call: the underlying
 * data never changes once the comparison set and prediction exist.
 */
export function revealPredictionComparison(sessionId: string): Promise<RevealComparison> {
  return apiFetch<RevealComparison>(`/sessions/${sessionId}/researcher/reveal`, {
    method: 'POST',
  });
}

/** Look up the comparison set's counter-case, if any. */
export function getSetCounterCase(sessionId: string): Promise<CounterCaseResponse> {
  return apiFetch<CounterCaseResponse>(`/sessions/${sessionId}/researcher/counter-case`);
}

/**
 * Submit the post-reveal contrast reflection. Safe to call repeatedly: the
 * backend derives contrast_type itself and returns the stored entry
 * afterwards.
 */
export function submitSetContrast(
  sessionId: string,
  learnerResponse: string | null,
): Promise<SetContrastResponse> {
  return postJson<SetContrastResponse>(`/sessions/${sessionId}/researcher/contrast`, {
    learner_response: learnerResponse,
  });
}

export function getResearcherSessionReport(sessionId: string): Promise<ResearcherSessionReport> {
  return apiFetch<ResearcherSessionReport>(`/sessions/${sessionId}/researcher/report`);
}

export function getResearcherCaseDetail(
  sessionId: string,
  caseId: string,
): Promise<ResearcherCaseDetail> {
  return apiFetch<ResearcherCaseDetail>(`/sessions/${sessionId}/researcher/cases/${caseId}`);
}
