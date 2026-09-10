/**
 * Placeholder content for the M0 intake and self-assessment.
 *
 * NOT VALIDATED ASSESSMENT MATERIAL. The items, the primer and the correction
 * text are stand-ins written to exercise the flow, not to measure anything.
 * `PLACEHOLDER_NOTICE` says so on screen, deliberately: a learner should never
 * be left thinking this scored them meaningfully.
 *
 * No option here carries an `isCorrect` flag, and none ever should. The
 * backend's api/content/intake_key.py is the sole holder of the answer key;
 * this file supplies only what is displayed. The two are joined by the item
 * and option ids below, kept aligned by hand -- change an id here and it must
 * change there in the same commit.
 *
 * Content lives here rather than in i18n for the same reason framing.ts does:
 * the ids are a wire contract and must not vary by locale. That leaves the
 * copy English-only for now, which is acceptable while it is a placeholder.
 */

export interface IntakeOption {
  /** Sent to the backend verbatim. Never translate or rename casually. */
  value: string;
  label: string;
}

export interface IntakeItem {
  /** Sent to the backend verbatim, and positional: order matters. */
  id: string;
  prompt: string;
  options: readonly IntakeOption[];
}

export const PLACEHOLDER_NOTICE =
  'Temporary placeholder, not a validated assessment. These questions and the ' +
  'result they produce are scaffolding for development and carry no judgement ' +
  'about your understanding.';

/**
 * The three diagnostic items, in submission order.
 *
 * The API takes a bare array of selected option ids, matched to items by
 * position, so this order is part of the contract with the backend's
 * DIAGNOSTIC_ITEMS.
 */
export const DIAGNOSTIC_ITEMS: readonly IntakeItem[] = [
  {
    id: 'd1',
    prompt: 'Placeholder: what makes a piece of research "dual-use"?',
    options: [
      { value: 'd1a', label: 'It is funded by more than one organisation.' },
      { value: 'd1b', label: 'It has been published in two different venues.' },
      {
        value: 'd1c',
        label: 'The same capability can serve both beneficial and harmful ends.',
      },
      { value: 'd1d', label: 'It combines two or more scientific disciplines.' },
    ],
  },
  {
    id: 'd2',
    prompt: 'Placeholder: when is the earliest useful point to consider downstream misuse?',
    options: [
      { value: 'd2a', label: 'While choosing the problem, before any work begins.' },
      { value: 'd2b', label: 'At peer review, once the method is fixed.' },
      { value: 'd2c', label: 'After publication, if concerns are raised.' },
      { value: 'd2d', label: 'Only if a funder or ethics body asks.' },
    ],
  },
  {
    id: 'd3',
    prompt:
      'Placeholder: what does releasing a capability as an API rather than open weights mainly change?',
    options: [
      { value: 'd3a', label: 'The scientific validity of the result.' },
      { value: 'd3b', label: 'How much control the originator keeps over downstream use.' },
      { value: 'd3c', label: 'Whether the work counts as a publication.' },
      { value: 'd3d', label: 'The cost of reproducing the experiment.' },
    ],
  },
];

/**
 * Shown only to learners who score below the backend's threshold. Skipped
 * silently for everyone else -- there is no endpoint for it either way.
 */
export const MICRO_PRIMER = {
  title: 'A short primer before you start',
  body:
    'Placeholder primer. Dual-use research is work whose capability can serve ' +
    'both beneficial and harmful ends, often without any change to the work ' +
    'itself. The questions that follow ask you to notice where in a project ' +
    'that possibility becomes visible, and who is positioned to act on it. ' +
    'Real primer content is still to be written.',
} as const;

export const COMPREHENSION_CHECK: IntakeItem = {
  id: 'c1',
  prompt:
    'Placeholder: a team releases an image-generation model as openly ' +
    'downloadable weights instead of providing controlled access through ' +
    'an API, and the model is later used to create non-consensual ' +
    'synthetic images. At which decision point could the risk most ' +
    'plausibly have been addressed?',
  options: [
    { value: 'c1a', label: 'After the harmful images were reported.' },
    { value: 'c1b', label: 'When deciding how to release the model.' },
    { value: 'c1c', label: 'It could not have been addressed at any point.' },
  ],
};

/**
 * Static content shown after a wrong comprehension answer. It replaces a
 * second attempt: the backend has already finalized the intake by this point,
 * and nothing here is resubmitted.
 */
export const TARGETED_CORRECTION = {
  title: 'Not quite',
  body:
    'Placeholder correction. The release decision is usually the last point at ' +
    'which the originator still has meaningful control: once a capability is ' +
    'distributed, the choices left are other people’s. Reacting after ' +
    'reported misuse is real work, but it is no longer prevention. Real ' +
    'targeted-correction content is still to be written.',
} as const;
