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
 * development database. `globalSetup` creates, resets, migrates and seeds it
 * before any test runs; see e2e/global-setup.ts.
 */

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 9000;

/** Must match public/env.js, which hardcodes the API origin the app calls. */
export const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
export const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

/** The only database this suite is ever allowed to touch. */
const E2E_DB_NAME = 'app_e2e';

const backendDir = fileURLToPath(new URL('../backend', import.meta.url));

/**
 * The Makefile's `dotenv run` wrapper is deliberately bypassed here so
 * DB_NAME cannot be overridden back to the development database -- but
 * Config() (api/config.py) now reads `.env` directly itself via
 * pydantic-settings' env_file, independent of any wrapper. So the real
 * repo-root `.env` (including its real Google OAuth credentials) would
 * otherwise reach this spawned backend for anything not explicitly set
 * below. GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are forced to the empty
 * string, not merely left unset, to actually keep OAuth dormant here --
 * see google_oauth_configured()'s docstring (api/services/auth.py) for
 * why unset alone would not be enough once env_file is in the picture.
 */
const backendEnv = {
  DB_NAME: E2E_DB_NAME,
  SECRET_KEY: 'e2e-secret-key-not-used-for-anything',
  // Required by config.Config with no default, though no test path calls the
  // model. A placeholder keeps startup from failing.
  OPENAI_API_KEY: 'e2e-placeholder-key',
  // Force the OAuth routes dormant for e2e: no test drives a "Sign in with
  // Google" flow (there is no button for it yet), and a real backend
  // reachable at localhost:8000 should never carry a developer's real
  // Google OAuth credentials during an automated run.
  GOOGLE_CLIENT_ID: '',
  GOOGLE_CLIENT_SECRET: '',
};

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
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
      // No --reload: the watcher restarts the server mid-test.
      command: `uv run uvicorn api.main:app --port ${BACKEND_PORT}`,
      cwd: backendDir,
      url: `${BACKEND_URL}/healthz`,
      env: backendEnv,
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
