import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * M5: the post-reveal contrast reflection and the "another case?" loop.
 *
 * Uses the dev bypass (`/student`) rather than the real front door: the M0
 * intake flow itself is already covered end-to-end by happy-path.spec.ts,
 * and duplicating it here would only make these tests slower and more
 * fragile without adding coverage of what this file is actually about.
 */

async function startSessionViaDevBypass(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('link', { name: 'Skip to student flow (dev)' }).click();
  await page.getByRole('button', { name: 'Start a session' }).click();
  await expect(page.getByText('Session in progress')).toBeVisible();
}

/** Open the confirm dialog for the first still-listed case and confirm it. */
async function pickFirstAvailableCase(page: Page): Promise<void> {
  const firstCase = page.getByRole('button', { name: 'Work on this case' }).first();
  await expect(firstCase).toBeVisible();
  await firstCase.click();
  await expect(page.getByText('Start this case?')).toBeVisible();
  await page.getByRole('button', { name: 'Start this case' }).click();
  await expect(page.getByText('The situation')).toBeVisible();
}

/** Pick a specific case by its title, for tests that need a known branch. */
async function pickCaseByTitle(page: Page, title: string): Promise<void> {
  const card = page.locator('.q-card', { hasText: title }).first();
  await card.getByRole('button', { name: 'Work on this case' }).click();
  await expect(page.getByText('Start this case?')).toBeVisible();
  await page.getByRole('button', { name: 'Start this case' }).click();
  await expect(page.getByText('The situation')).toBeVisible();
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

/** Commit with a fixed pattern/gate (match result is irrelevant here), then reveal. */
async function commitAndReveal(page: Page): Promise<void> {
  await chooseFromSelect(page, 'Pattern', /^A —/);
  // 'Decision gate' also matches the framing question above it
  // ("At which decision gate does this choice occur?"); exact-match the
  // commitment select, same as happy-path.spec.ts.
  await chooseFromSelect(page, 'Decision gate', /^G1/, true);

  await page.getByRole('button', { name: 'Commit', exact: true }).click();
  await expect(page.getByText('Commitment saved. You can now reveal the case.')).toBeVisible();

  await page.getByRole('button', { name: 'Reveal the case' }).click();
  await expect(page.getByText(/^Revealed at /)).toBeVisible();
}

/**
 * Whichever contrast branch shows up, get past it: fill and submit the
 * reflection for a twin counter-case, or just wait out the automatic
 * open-area acknowledgement.
 */
async function completeWhicheverContrastBranch(page: Page): Promise<void> {
  const twinTitle = page.getByText('A counter-case exists');
  const openAreaMessage = page.getByText(/This area is not yet covered by a counter-case/);
  await expect(twinTitle.or(openAreaMessage)).toBeVisible();

  if (await twinTitle.isVisible()) {
    await page.getByLabel('Your reflection').fill('A reflection for the e2e test.');
    await page.getByRole('button', { name: 'Submit', exact: true }).click();
  }
}

test('a case with a counter-case requires a reflection and survives reload', async ({ page }) => {
  await startSessionViaDevBypass(page);
  await pickCaseByTitle(page, 'Demo: Sensitive Research Disclosure');
  await commitAndReveal(page);

  await expect(page.getByText('A counter-case exists')).toBeVisible();
  const submit = page.getByRole('button', { name: 'Submit', exact: true });
  await expect(submit).toBeDisabled();

  await page.getByLabel('Your reflection').fill('The team that chose the release path.');
  await expect(submit).toBeEnabled();
  await submit.click();

  await expect(page.getByText('Reflection saved.')).toBeVisible();
  await expect(page.getByText('You have completed 1 of 3 case reflections.')).toBeVisible();

  await page.reload();

  await expect(page.getByText('A counter-case exists')).toBeVisible();
  await expect(page.getByText('Reflection saved.')).toBeVisible();
  await expect(page.getByText('You have completed 1 of 3 case reflections.')).toBeVisible();

  await page.getByRole('button', { name: 'Yes, another case' }).click();
  await expect(page).toHaveURL(/\/student$/);
  await expect(page.getByText('Session in progress')).toBeVisible();
});

test('a case with no counter-case submits the open-area acknowledgement automatically', async ({
  page,
}) => {
  await startSessionViaDevBypass(page);
  await pickCaseByTitle(page, 'Demo: Open Capability Release');
  await commitAndReveal(page);

  // No button to click: the honest-boundary message appears and the
  // acknowledgement is submitted on its own.
  await expect(page.getByText(/This area is not yet covered by a counter-case/)).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Your reflection' })).toHaveCount(0);
  await expect(page.getByText('You have completed 1 of 3 case reflections.')).toBeVisible();
});

test('the third encounter offers only Finish, landing on the temporary completion page', async ({
  page,
}) => {
  await startSessionViaDevBypass(page);

  for (const current of [1, 2]) {
    await pickFirstAvailableCase(page);
    await commitAndReveal(page);
    await completeWhicheverContrastBranch(page);
    await expect(
      page.getByText(`You have completed ${current} of 3 case reflections.`),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Yes, another case' }).click();
    await expect(page).toHaveURL(/\/student$/);
  }

  await pickFirstAvailableCase(page);
  await commitAndReveal(page);
  await completeWhicheverContrastBranch(page);
  await expect(page.getByText('You have completed 3 of 3 case reflections.')).toBeVisible();

  await expect(page.getByRole('button', { name: 'Yes, another case' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'No', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Finish' }).click();

  await expect(page).toHaveURL(/\/student\/complete$/);
  await expect(
    page.getByText('TEMPORARY: the post-session debrief (M6) does not exist yet.'),
  ).toBeVisible();
});
