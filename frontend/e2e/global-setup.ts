import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

/**
 * Prepare the E2E database before any test, and before the servers start.
 *
 * Three steps, in this order:
 *
 *   1. reset   - create `app_e2e` if absent, then TRUNCATE session CASCADE so
 *                no run inherits sessions, intakes, encounters, commitments or
 *                feedback records from the last one. Case content survives.
 *   2. migrate - bring the schema to head.
 *   3. seed    - insert the demo cases (idempotent, keyed by title).
 *
 * Reset comes first because on a brand-new database there is nothing to
 * migrate yet; the reset script handles the absent-table case itself.
 *
 * Every command is given DB_NAME explicitly and bypasses the Makefile's
 * `dotenv run` wrapper, which would load ../.env and put DB_NAME back to the
 * development database. The reset script refuses to run against anything not
 * named `app_e2e*`, so a mistake here fails loudly rather than destructively.
 */

const E2E_DB_NAME = 'app_e2e';

const backendDir = fileURLToPath(new URL('../../backend', import.meta.url));

const env = {
  ...process.env,
  DB_NAME: E2E_DB_NAME,
  SECRET_KEY: 'e2e-secret-key-not-used-for-anything',
  OPENAI_API_KEY: 'e2e-placeholder-key',
};

const STEPS: ReadonlyArray<{ label: string; args: string[] }> = [
  { label: 'reset', args: ['run', 'python', '-m', 'scripts.reset_e2e'] },
  { label: 'migrate', args: ['run', 'alembic', 'upgrade', 'head'] },
  { label: 'seed', args: ['run', 'python', '-m', 'scripts.seed_cases'] },
];

export default function globalSetup(): void {
  for (const { label, args } of STEPS) {
    process.stdout.write(`[e2e setup] ${label} (${E2E_DB_NAME})\n`);
    execFileSync('uv', args, { cwd: backendDir, env, stdio: 'inherit' });
  }
}
