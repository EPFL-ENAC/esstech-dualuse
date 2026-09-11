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
 * The backend reads settings straight from the environment; it does not load
 * `.env` itself (that is done by the `dotenv run` wrapper in the Makefile,
 * which is deliberately bypassed here so DB_NAME cannot be overridden back to
 * the development database).
 */
const backendEnv = {
  DB_NAME: E2E_DB_NAME,
  SECRET_KEY: 'e2e-secret-key-not-used-for-anything',
  // Required by config.Config with no default, though no test path calls the
  // model. A placeholder keeps startup from failing.
  OPENAI_API_KEY: 'e2e-placeholder-key',
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
