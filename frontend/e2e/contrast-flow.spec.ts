import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

import { BACKEND_URL } from '../playwright.config';

/**
 * The post-reveal contrast reflection and the "another case?" loop.
 *
 * Opens `/student` directly rather than going through the real front door:
 * the intake is covered end-to-end by happy-path.spec.ts.
 */

async function startSessionDirectly(page: Page): Promise<void> {
  await page.goto('/student');
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

/**
 * Spend this learner's first `count` candidate cases through the API, so the
 * cases after them are offered next. page.request shares the browser's
 * cookies, so the API calls run as the same dev learner.
 */
async function consumeCandidates(page: Page, count: number): Promise<void> {
  const session = (await (await page.request.post(`${BACKEND_URL}/sessions`)).json()) as {
    id: string;
  };
  const candidates = (await (await page.request.get(`${BACKEND_URL}/cases/candidates`)).json()) as {
    id: string;
  }[];
  for (const candidate of candidates.slice(0, count)) {
    await page.request.post(`${BACKEND_URL}/sessions/${session.id}/encounters`, {
      data: { case_id: candidate.id },
    });
  }
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
async function chooseFromSelect(page: Page, label: string, optionText: RegExp): Promise<void> {
  await page.getByRole('combobox', { name: label }).first().click();
  await page.getByRole('option').filter({ hasText: optionText }).first().click();
}

/** Commit with a fixed pattern/gate (match result is irrelevant here), then reveal. */
async function commitAndReveal(page: Page): Promise<void> {
  await chooseFromSelect(page, 'Pattern', /^A —/);
  await chooseFromSelect(page, 'Decision gate', /^G1/);

  await page.getByRole('button', { name: 'Commit', exact: true }).click();
  await expect(page.getByText('Commitment saved. You can now reveal the case.')).toBeVisible();

  await page.getByRole('button', { name: 'Reveal the case' }).click();
  await expect(page.getByText(/^Revealed at /)).toBeVisible();
}

/**
 * Whichever contrast branch shows up, get past it: fill and submit the
 * reflection for a twin counter-case, or just wait out the automatic
 * open-area acknowledgement, which shows no message of its own.
 */
async function completeWhicheverContrastBranch(page: Page): Promise<void> {
  const twinTitle = page.getByText('A counter-case exists');
  const completed = page.getByText(/^You have completed \d of 3 case reflections\.$/);
  await expect(twinTitle.or(completed)).toBeVisible();

  if (await twinTitle.isVisible()) {
    await page.getByLabel('Your reflection').fill('A reflection for the e2e test.');
    await page.getByRole('button', { name: 'Submit', exact: true }).click();
  }
}

test('a case with a counter-case requires a reflection and survives reload', async ({ page }) => {
  // A new learner is offered the oldest three unseen published harm cases,
  // none of which has a counter-case; spending them puts RepRap on offer.
  await consumeCandidates(page, 3);
  await startSessionDirectly(page);
  await pickCaseByTitle(page, 'RepRap');
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
  await startSessionDirectly(page);
  await pickCaseByTitle(page, 'MIT Institute for Soldier Nanotechnologies');
  await commitAndReveal(page);

  // No question to answer: the acknowledgement is submitted on its own.
  await expect(page.getByRole('textbox', { name: 'Your reflection' })).toHaveCount(0);
  await expect(page.getByText('You have completed 1 of 3 case reflections.')).toBeVisible();
});

test('the third encounter offers only Finish, landing on the session debrief', async ({ page }) => {
  await startSessionDirectly(page);

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
  await expect(page.getByText('Your session debrief')).toBeVisible();
  await expect(page.getByText('Cases explored')).toBeVisible();
  await expect(page.getByText(/TEMPORARY/)).toHaveCount(0);
});
