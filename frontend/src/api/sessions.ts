/** Typed client for the /sessions endpoint, shared by both routes. */
import { postJson } from 'boot/api';

export type SessionRoute = 'student' | 'researcher';
export type SessionMode = 'individual' | 'group' | 'lecture';

export interface SessionCreated {
  id: string;
  route: SessionRoute;
  mode: SessionMode;
  started_at: string;
}

export function createSession(route: SessionRoute): Promise<SessionCreated> {
  return postJson<SessionCreated>('/sessions', { route });
}
