/**
 * Typed client for the Researcher/Individual endpoints.
 *
 * The types mirror the backend's response models exactly, the same
 * convention as api/student.ts and api/intake.ts. Session creation itself
 * lives in api/sessions.ts, not here -- it is shared by both routes.
 */
import { apiFetch } from 'boot/api';
import type { Gate } from 'src/api/student';

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
