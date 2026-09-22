import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

import {
  COMPREHENSION_CHECK,
  DIAGNOSTIC_ITEMS,
  MICRO_PRIMER,
} from '../src/content/intake';

/**
 * The full learner happy path, in a real browser.
 *
 * This covers the seams that unit and integration tests structurally cannot:
 *
 *   - the `dev_learner_id` cookie surviving a genuine cross-origin round trip
 *     (frontend on :9000, API on :8000) rather than a mocked fetch
 *   - the payloads the frontend actually builds matching what the API accepts,
 *     including the enum ids behind the display labels
 *   - session and encounter ids surviving real navigation and a real reload
 *   - the anti-spoiler boundary holding under an actual page load: the case's
 *     main path must not reach the browser before the reveal
 *   - reveal staying compute-or-fetch when the browser asks a second time
 *
 * Correct-answer hints are an intentional part of the learner-facing UI, but
 * they are guidance rather than a gate: a learner may continue after errors.
 */

/** Pick the first option of every diagnostic item, including likely errors. */
async function answerDiagnostic(page: Page): Promise<void> {
  for (const item of DIAGNOSTIC_ITEMS) {
    const first = item.options[0];
    expect(first, `item ${item.id} has no options`).toBeDefined();
    await page.getByRole('radio', { name: first!.label, exact: true }).check();
  }
}

/** Quasar selects are not native <select>: open the menu, then click an option. */
async function chooseFromSelect(
  page: Page,
  label: string,
  optionText: RegExp,
  exact = false,
): Promise<void> {
  await page.getByRole('combobox', { name: label, exact }).first().click();
  await page.getByRole('option').filter({ hasText: optionText }).first().click();
}

test('a learner completes intake, commits to a case, and the reveal never changes', async ({
  page,
}) => {
  // --- M1 route choice, then M0 intake, entered through the real front
  // door, not the dev bypass ---
  await page.goto('/');
  await page.getByRole('link', { name: 'Start session' }).click();
  await page.getByRole('button', { name: 'Continue as a student' }).click();
  await expect(page.getByText('Before you begin')).toBeVisible();

  await answerDiagnostic(page);
  await page.getByRole('button', { name: 'Check answers' }).click();
  await expect(page.getByText('A hint before you continue')).toBeVisible();
  await expect(page.getByText(/continue when you are ready/i)).toBeVisible();
  await page.getByRole('button', { name: 'Continue', exact: true }).click();

  // The primer appears only below the score threshold, which depends on an
  // answer key this test cannot see. Both branches are legitimate.
  const primer = page.getByText(MICRO_PRIMER.title);
  const comprehensionTitle = page.getByText('One last check');
  await expect(primer.or(comprehensionTitle)).toBeVisible();
  if (await primer.isVisible()) {
    await page.getByRole('button', { name: 'Got it, continue' }).click();
  }

  // --- comprehension check: an error teaches, but does not block ---
  await expect(comprehensionTitle).toBeVisible();
  const firstOption = COMPREHENSION_CHECK.options[0];
  expect(firstOption).toBeDefined();
  await page.getByRole('radio', { name: firstOption!.label, exact: true }).check();
  await page.getByRole('button', { name: 'Check answers' }).click();

  const doneTitle = page.getByText('You are set up');
  await expect(page.getByText('Take another look')).toBeVisible();
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(doneTitle).toBeVisible();
  await page.getByRole('button', { name: 'Choose a case' }).click();

  // --- Student / Individual: the intake already started the session, so the
  // "Start a session" card must not be offered again ---
  await expect(page.getByText('Session in progress')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start a session' })).toHaveCount(0);

  // --- pick a case, through the confirmation dialog ---
  const firstCase = page.getByRole('button', { name: 'Work on this case' }).first();
  await expect(firstCase).toBeVisible();
  await firstCase.click();
  await expect(page.getByText('Start this case?')).toBeVisible();
  await page.getByRole('button', { name: 'Start this case' }).click();

  await expect(page.getByText('The situation')).toBeVisible();

  // The answer key must not have reached the browser yet. `main_path_pattern`
  // is the field name the reveal response uses; before the reveal it should
  // appear nowhere in the rendered page.
  const preRevealHtml = await page.content();
  expect(preRevealHtml).not.toContain('main_path_pattern');
  expect(preRevealHtml).not.toContain('full_narrative');

  // --- framing answers, then the commitment ---
  const textareas = page.locator('textarea');
  const textareaCount = await textareas.count();
  for (let index = 0; index < textareaCount; index += 1) {
    await textareas.nth(index).fill(`E2E answer ${index + 1}`);
  }
  await chooseFromSelect(page, 'At which decision gate', /^G1/);
  await chooseFromSelect(page, 'Pattern', /^A —/);
  // Plain 'Decision gate' would also match the framing question above
  // ("At which decision gate does this choice occur?"), whose accessible
  // name contains it as a substring; exact-match the commitment select.
  await chooseFromSelect(page, 'Decision gate', /^G1/, true);

  await page.getByRole('button', { name: 'Commit', exact: true }).click();
  await expect(page.getByText('Commitment saved. You can now reveal the case.')).toBeVisible();

  // --- reveal ---
  await page.getByRole('button', { name: 'Reveal the case' }).click();
  const revealedAt = page.getByText(/^Revealed at /);
  await expect(revealedAt).toBeVisible();

  const firstTimestamp = await revealedAt.innerText();
  const firstVerdict = await page.locator('.reveal-panel .text-h6').innerText();

  // --- reload, then ask the server again ---
  await page.reload();

  // The store is persisted, so the panel comes back from local state alone.
  // That proves navigation survives a reload, but says nothing about the
  // backend, so the next step asks the API a second time on purpose.
  await expect(page.getByText(/^Revealed at /)).toBeVisible();

  await page.getByRole('button', { name: 'Show again' }).click();

  // Compute-or-fetch: the second POST must return the stored verdict, with the
  // original timestamp, rather than recomputing and restamping it.
  await expect(page.getByText(/^Revealed at /)).toHaveText(firstTimestamp);
  await expect(page.locator('.reveal-panel .text-h6')).toHaveText(firstVerdict);

  // Start over must leave the old session and return to the first questions,
  // including after a reload (the stores are persisted in the browser).
  await page.goto('/student');
  await page.getByRole('button', { name: 'Start over' }).click();
  await expect(page).toHaveURL(/\/intake$/);
  await expect(page.getByText('Before you begin')).toBeVisible();
  await expect(page.getByText('Three quick questions')).toBeVisible();
  await page.reload();
  await expect(page.getByText('Three quick questions')).toBeVisible();
});
