/**
 * Typed client for the generic /sessions endpoint.
 *
 * Split out of api/student.ts: session creation is shared by both routes
 * (RouteChoicePage.vue creates a Researcher-route session the same way
 * IntakePage.vue lazily creates a Student-route one), so it has no business
 * living in a file documented as Student/Individual-only.
 */
import { apiFetch } from 'boot/api';

export type SessionRoute = 'student' | 'researcher';
export type SessionMode = 'individual' | 'group' | 'lecture';

export interface SessionCreated {
  id: string;
  route: SessionRoute;
  mode: SessionMode;
  started_at: string;
}

/**
 * Start a session. Omitting `route` matches the backend's own default
 * (Student) and sends the exact bodyless POST every existing caller already
 * sends -- passing 'student' explicitly would be equivalent, but this keeps
 * those call sites byte-for-byte unchanged.
 */
export function createSession(route?: SessionRoute): Promise<SessionCreated> {
  if (route === undefined) {
    return apiFetch<SessionCreated>('/sessions', { method: 'POST' });
  }
  return apiFetch<SessionCreated>('/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ route }),
  });
}
