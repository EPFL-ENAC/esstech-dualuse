/**
 * Typed client for the Researcher/Individual endpoints.
 *
 * The types mirror the backend's response models exactly, the same
 * convention as api/student.ts and api/intake.ts. Session creation itself
 * lives in api/sessions.ts, not here -- it is shared by both routes.
 */
import { apiFetch } from 'boot/api';
import type { ContrastType, Gate, Pattern } from 'src/api/student';

export type Domain =
  | 'Material Science'
  | 'Advanced Manufacturing / 3D Printing'
  | 'Semiconductors and Nanotechnology'
  | 'Artificial Intelligence'
  | 'Cyber Technologies'
  | 'Quantum Technology'
  | 'Robotics & Autonomous Systems'
  | 'Neurotechnology'
  | 'Biochemistry';

export type Function =
  | 'sensing'
  | 'generating'
  | 'controlling'
  | 'predicting'
  | 'editing'
  | 'optimizing'
  | 'fabricating'
  | 'computing';

export type Form =
  | 'platform'
  | 'model'
  | 'dataset'
  | 'protocol'
  | 'device'
  | 'infrastructure'
  | 'material'
  | 'method';

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
  attempts_remaining: number;
  gate: Gate | null;
  posture_response: string | null;
  created_at: string;
}

/** The outcome of one /tag attempt: current mapping state, and whether
 * another attempt remains. */
export interface TagResult {
  domain: Domain | null;
  functions: Function[];
  forms: Form[];
  mapping_status: MappingStatus;
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

/** One ranked pattern in a submitted prediction set. */
export interface PredictionEntry {
  rank: number;
  pattern: Pattern;
}

export interface PredictionSubmissionResult {
  predictions: PredictionEntry[];
}

/**
 * A session's prediction compared against its comparison set's tagged
 * pattern distribution. Structured facts about two independently-stored
 * things, not a verdict -- same framing as Student's reveal.
 */
export interface RevealComparison {
  dominant_pattern: Pattern | null;
  secondary_patterns: Pattern[];
  predictions: PredictionEntry[];
  top_prediction_is_dominant: boolean;
  predictions_in_secondary: Pattern[];
  predictions_not_activated: Pattern[];
}

/** The counter-case fields shown before the set-level WHO reflection. */
export interface SetCounterCaseInfo {
  counter_case_id: string;
  gate_lever: Gate;
  responsibility_posture_contrast: string;
}

/** Whether the session's comparison set has a linked counter-case. */
export interface SetCounterCaseResponse {
  has_counter_case: boolean;
  counter_case: SetCounterCaseInfo | null;
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
 * The Researcher-route debrief: a read-only aggregation over the session's
 * technology intake, comparison set, prediction, and set-level contrast.
 *
 * Every field below is absent, not null, unless trace_completeness has
 * actually reached the point that field is meaningful -- absent means "not
 * reached yet", never "empty result". A list-typed field can still
 * legitimately be an empty array once present (e.g. secondary_patterns: []
 * in a real "full" report where nothing secondary activated).
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
  reflection_prompt_key?: string;
}

/**
 * One case from a session's comparison set, with why it was included.
 *
 * Deliberately narrower pre-prediction: full_narrative, main_path_pattern,
 * main_path_gate, and source_references are the answer key, absent (not
 * null) until the session has a submitted prediction -- same
 * exclude_none convention as ResearcherSessionReport.
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

function postJson<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/**
 * Start the session's technology intake from its free-text description.
 *
 * One-shot: a second call for a session that already has an intake is
 * rejected. The mapping loop happens in submitTag, not here.
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
 * resume mid-flow. A 404 is the ordinary "not started yet" case, not an
 * error -- callers should treat it the same way getIntake's 404 is treated
 * in IntakePage.vue.
 */
export function getTechnologyIntake(sessionId: string): Promise<TechnologyIntakeState> {
  return apiFetch<TechnologyIntakeState>(`/sessions/${sessionId}/researcher/intake`);
}

/**
 * Submit one /tag attempt. Bounded to two total attempts by the backend --
 * this call never needs to track the budget itself, attempts_remaining on
 * the result says how many are left.
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
 *
 * Idempotent: computed once, then returned unchanged on every later call,
 * the same as Student's reveal.
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

/**
 * Look up the comparison set's counter-case, if any.
 *
 * Never a 404 for "no counter-case" -- that is a valid corpus state,
 * reported as `has_counter_case: false`, not an error. Mirrors
 * getCounterCase (api/student.ts).
 */
export function getSetCounterCase(sessionId: string): Promise<SetCounterCaseResponse> {
  return apiFetch<SetCounterCaseResponse>(`/sessions/${sessionId}/researcher/counter-case`);
}

/**
 * Submit the post-reveal contrast reflection.
 *
 * Safe to call repeatedly: the backend derives contrast_type itself and
 * returns the stored entry afterwards, the same as Student's submitContrast.
 */
export function submitSetContrast(
  sessionId: string,
  learnerResponse: string | null,
): Promise<SetContrastResponse> {
  return postJson<SetContrastResponse>(`/sessions/${sessionId}/researcher/contrast`, {
    learner_response: learnerResponse,
  });
}

/**
 * Get the session's debrief and report: a read-only aggregation over the
 * technology intake, comparison set, prediction, and set-level contrast.
 */
export function getResearcherSessionReport(sessionId: string): Promise<ResearcherSessionReport> {
  return apiFetch<ResearcherSessionReport>(`/sessions/${sessionId}/researcher/report`);
}

/**
 * Get one case from the session's comparison set, with why it was
 * included. The answer key fields are absent until the session has a
 * submitted prediction.
 */
export function getResearcherCaseDetail(
  sessionId: string,
  caseId: string,
): Promise<ResearcherCaseDetail> {
  return apiFetch<ResearcherCaseDetail>(`/sessions/${sessionId}/researcher/cases/${caseId}`);
}
