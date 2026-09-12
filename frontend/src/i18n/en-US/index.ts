export default {
  appTitle: 'esstech-dualuse',

  goHome: 'Go home',
  notFoundMessage: 'Sorry, nothing here...',

  welcome: 'Welcome to the boilerplate',
  welcomeHint: 'This is the dummy home page. Replace it with your real content.',
  fetchMessage: 'Fetch backend message',

  sessionStart: 'Start session',
  studentOpenDev: 'Skip to student flow (dev)',

  intakeTitle: 'Before you begin',
  intakeIntro: 'A few quick questions to set up your session.',
  intakeDiagnosticTitle: 'Three quick questions',
  intakeComprehensionTitle: 'One last check',
  intakeOneAttempt: 'One attempt only — you will not be asked again.',
  intakeSubmit: 'Continue',
  intakeSubmitting: 'Saving...',
  intakePrimerContinue: 'Got it, continue',
  intakeContinue: 'Continue',
  intakeDoneTitle: 'You are set up',
  intakeDoneBody: 'Your session is ready. Next, choose a case to work through.',
  intakeGoToCases: 'Choose a case',

  studentTitle: 'Student — individual',
  studentIntro: 'Work through up to three cases, one decision at a time.',
  studentStart: 'Start a session',
  studentStarting: 'Starting your session...',
  studentSessionActive: 'Session in progress',
  studentReset: 'Start over',

  casesTitle: 'Choose a case',
  casesLoading: 'Loading cases...',
  casesEmpty: 'No cases left. You have worked through everything available.',
  caseSelect: 'Work on this case',
  caseSelecting: 'Opening case...',
  confirmSelectTitle: 'Start this case?',
  confirmSelectBody:
    'Opening "{title}" uses one of the three cases in this session. It cannot be undone.',
  confirmSelect: 'Start this case',
  confirmCancel: 'Cancel',

  encounterTitle: 'The situation',
  encounterMissing: 'No case is open. Pick one to continue.',
  encounterStep: 'Case {current} of {total}',

  framingTitle: 'Before you commit',
  framingHint: 'Answer in your own words. These are saved with your commitment.',

  commitmentTitle: 'Your reading',
  commitmentPattern: 'Pattern',
  commitmentGate: 'Decision gate',
  commitmentHint: 'Choose the pattern and the gate you think this case turns on.',
  commitmentSubmit: 'Commit',
  commitmentSubmitting: 'Saving your commitment...',
  commitmentSaved: 'Commitment saved. You can now reveal the case.',
  commitmentIncomplete: 'Choose a pattern and a gate first.',

  revealAction: 'Reveal the case',
  revealLoading: 'Revealing...',
  revealTitle: 'What happened',
  revealYourReading: 'Your reading',
  revealMainPath: 'Main path',
  revealSources: 'Sources',
  revealAt: 'Revealed at {at}',
  revealAgain: 'Show again',

  contrastContinue: 'Continue',
  contrastTwinTitle: 'A counter-case exists',
  contrastWhoQuestion:
    'What was different about who held responsibility in this counter-case, compared to the case you just read?',
  contrastResponseLabel: 'Your reflection',
  contrastSubmit: 'Submit',
  contrastSubmitting: 'Saving...',
  contrastSaved: 'Reflection saved.',
  contrastOpenAreaMessage:
    'This area is not yet covered by a counter-case in the current corpus. The tool does not infer a solution where the evidence base has none.',

  anotherCaseProgress: 'You have completed {current} of {total} case reflections.',
  anotherCaseYes: 'Yes, another case',
  anotherCaseNo: 'No',
  anotherCaseFinish: 'Finish',

  completeTitle: 'Your session debrief',
  completeBody: 'A summary of your case reflections in this session.',
  completeGoHome: 'Return home',
  completeNoCasesBody: 'You have not completed any case reflections in this session yet.',
  completeCasesExploredLabel: 'Cases explored',
  completeDecisionPointsLabel: 'Decision gates considered',
  completePatternsSelectedLabel: 'Patterns selected',
  completeMatchBreakdownLabel: 'Match breakdown',
  completeCounterCaseReflectionsLabel: 'Counter-case reflections completed',
  completeSuggestedFocusLabel: 'Suggested next focus',

  scaffoldingLabel: 'Support level',
  scaffoldingPlaceholderNote:
    'Provisional placeholder, not a validated assessment of your understanding.',
  scaffoldingHigh: 'High support needed',
  scaffoldingStandard: 'Standard support needed',
  scaffoldingLow: 'Minimal support needed',

  matchMatch: 'Match',
  matchPartial: 'Partial match',
  matchMismatch: 'No match',
  matchMatchHint: 'You identified both the pattern and the gate.',
  matchPartialHint: 'You identified one of the two.',
  matchMismatchHint: 'Neither matched the case main path.',

  reflectionMatch:
    "You identified {pattern} at {gate}. Your interpretation aligned with the case's main path. Which secondary pattern or gate would you examine next, and why?",
  reflectionPartialMatch:
    "You identified {pattern} at {gate}. Your interpretation matched the case's main path on one of the two elements. Which one did you read correctly — the pattern or the gate — and what led you to the other one?",
  reflectionMismatch:
    "You identified {pattern} at {gate}. Your interpretation differed from the case's main path on both elements. What assumption led to your choice? Which part of the case evidence would you revisit?",

  errorTitle: 'Something went wrong',
  errorRetry: 'Try again',
  errorUnexpected: 'Unexpected error. Please try again.',
  errorNotYours: 'This is no longer available. Start a new session to continue.',
};
