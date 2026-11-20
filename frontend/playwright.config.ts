import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

/**
 * End-to-end configuration.
 *
 * These tests are deliberately NOT wired into lefthook's pre-commit hooks:
 * they need two live servers and a database, and take orders of magnitude
 * longer than the static checks. They run only through `npm run test:e2e`.
 * Do not add an `e2e` command to lefthook.yml.
 *
 * Everything here targets a dedicated `app_e2e` database, never the local
 * development database. The backend server command resets, migrates and seeds
 * it before uvicorn starts (see backend/scripts/reset_e2e.py). It cannot be a
 * `globalSetup`: Playwright starts the web servers first, and the backend
 * refuses to start on a schema that is not at the latest migration.
 *
 * Postgres must already be running (`make run-db` from the repo root).
 */

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 9000;

/** Must match public/env.js, which hardcodes the API origin the app calls. */
export const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

/** The only database this suite is ever allowed to touch. */
const E2E_DB_NAME = 'app_e2e';

const backendDir = fileURLToPath(new URL('../backend', import.meta.url));

/**
 * The backend's Config() reads the repo-root `.env` itself (pydantic-settings
 * env_file); the real environment variables set here outrank it, and anything
 * not set here comes from the developer's real `.env`.
 *
 * Google OAuth is kept dormant: no test drives a Google sign-in, and an
 * automated run must never carry a developer's real OAuth credentials. The
 * credentials are set to the empty string rather than left unset, because
 * unset ones would be filled in from `.env`.
 */
const BACKEND_ENV = {
  DB_NAME: E2E_DB_NAME,
  SECRET_KEY: 'e2e-secret-key-not-used-for-anything',
  GOOGLE_CLIENT_ID: '',
  GOOGLE_CLIENT_SECRET: '',
};

export default defineConfig({
  testDir: './e2e',
  // The happy path walks a single learner through one linear flow; running
  // specs in parallel against one database would let them see each other's
  // sessions in the candidate list.
  fullyParallel: false,
  workers: 1,
  // A failed E2E run usually means a real regression, not a flake. Retrying
  // would hide an intermittent bug rather than report it.
  retries: 0,
  timeout: 60_000,
  reporter: [['list']],

  use: {
    baseURL: FRONTEND_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    locale: 'en-US',
  },

  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],

  webServer: [
    {
      // Reset first: a brand-new database has nothing to migrate, and the
      // reset script creates it. No --reload: the watcher restarts the
      // server mid-test.
      command: [
        'uv run python -m scripts.reset_e2e',
        'uv run alembic upgrade head',
        'uv run python -m scripts.seed_cases',
        `uv run uvicorn api.main:app --port ${BACKEND_PORT}`,
      ].join(' && '),
      cwd: backendDir,
      url: `${BACKEND_URL}/healthz`,
      env: BACKEND_ENV,
      // Never reuse: an already-running dev server is pointed at the
      // development database, and silently testing against it is the exact
      // failure this suite is meant to avoid. Stop `make run-backend` first.
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `quasar dev --port ${FRONTEND_PORT}`,
      url: FRONTEND_URL,
      reuseExistingServer: false,
      timeout: 120_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
