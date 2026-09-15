export default {
  appTitle: 'esstech-dualuse',

  goHome: 'Go home',
  notFoundMessage: 'Sorry, nothing here...',

  welcome: 'Welcome to the boilerplate',
  welcomeHint: 'This is the dummy home page. Replace it with your real content.',
  fetchMessage: 'Fetch backend message',

  sessionStart: 'Start session',
  studentOpenDev: 'Skip to student flow (dev)',

  routeChoiceTitle: 'Choose how to begin',
  routeChoiceIntro: 'Select the option that matches what you are here to do.',
  routeChoiceResearcherLabel: 'Researcher — individual',
  routeChoiceResearcherHint:
    'Describe a technology, map its function and form, and see how your prediction compares to similar cases.',
  routeChoiceStudentAction: 'Continue as a student',
  routeChoiceResearcherAction: 'Continue as a researcher',
  routeChoiceStarting: 'Starting...',

  researcherIntakeTitle: 'Technology intake',

  researcherDescriptionIntro: 'Describe the technology you are working on, in your own words.',
  researcherDescriptionHint: 'A few sentences on what it does and how it works is enough to start.',
  researcherDescriptionLabel: 'Description',
  researcherDescriptionSubmit: 'Continue',
  researcherDescriptionSubmitting: 'Saving...',

  researcherTagTitle: 'Map your technology',
  researcherTagIntro:
    'Domain, Function, and Form together place your technology in the case corpus.',
  researcherTagDomainLabel: 'Domain',
  researcherTagFunctionsLabel: 'Function(s)',
  researcherTagFormsLabel: 'Form(s)',
  researcherTagSubmit: 'Submit',
  researcherTagSubmitting: 'Saving...',
  researcherTagPartialNotice:
    'Domain, Function, and Form are not all set yet. Fill in what is missing and submit again.',
  researcherTagAttemptRemaining: 'One attempt remaining.',
  researcherTagRetry: 'Try again',
  researcherTagMappedTitle: 'Technology mapped',
  researcherTagMappedBody: 'Domain, Function, and Form are all set.',
  researcherTagContinue: 'Continue',
  researcherTagExhaustedTitle: 'Mapping could not be completed',
  researcherTagExhaustedBody:
    'Domain, Function, and Form could not all be confirmed in the attempts available. The tool does not infer a mapping where the description gives none.',
  researcherTagViewSummary: 'View session summary',

  researcherGateTitle: 'Decision gate and responsibility',
  researcherGateIntro: 'One last reflection before your prediction is compared to similar cases.',
  researcherGateQuestion: "Which gate does this technology's dual-use risk mainly turn on?",
  researcherGatePostureHint:
    'Beyond your own intended use, who else could make use of this technology?',
  researcherGateSubmit: 'Continue',
  researcherGateSubmitting: 'Saving...',
  researcherGateDoneTitle: 'Recorded',
  researcherGateDoneBody: 'Your gate and reflection are saved.',

  researcherComparisonSetTitle: 'Comparison set',
  researcherComparisonSetIntro: 'Match your technology against similar cases in the corpus.',
  researcherComparisonSetBuild: 'Build comparison set',
  researcherComparisonSetBuilding: 'Building...',
  researcherComparisonSetCaseCount: '{count} cases in your comparison set.',
  researcherComparisonSetWidenedNotice:
    "Not enough cases shared your technology's function, so this set was widened by domain to reach a minimum comparison size.",

  researcherInclusionReasonSharedFunction: "Matched your technology's function",
  researcherInclusionReasonWidenedByDomain: "Added by widening to your technology's domain",
  researcherCaseDetailBack: 'Back to comparison set',

  researcherPredictionTitle: 'Your prediction',
  researcherPredictionHint:
    'Rank the patterns you expect to be most active across this comparison set.',
  researcherPredictionRankLabel: 'Prediction {rank}',
  researcherPredictionRankOptional: 'Prediction 3 (optional)',
  researcherPredictionDuplicateError: 'Each prediction must be a different pattern.',
  researcherPredictionSubmit: 'Submit prediction',
  researcherPredictionSubmitting: 'Saving...',
  researcherPredictionSaved: 'Prediction saved.',

  researcherRevealAction: 'Reveal comparison',
  researcherRevealLoading: 'Revealing...',
  researcherRevealTitle: 'Pattern distribution',
  researcherRevealDominantLabel: 'Dominant pattern',
  researcherRevealSecondaryLabel: 'Secondary patterns',
  researcherRevealLowActivationMessage:
    'No pattern is activated across this comparison set. The tool does not infer a dominant pattern where the corpus has none.',
  researcherRevealYourPredictions: 'Your predictions',
  researcherRevealTopMatchesDominant: 'Your top prediction matches the dominant pattern.',
  researcherRevealTopDoesNotMatchDominant:
    'Your top prediction does not match the dominant pattern.',
  researcherRevealInSecondaryLabel: 'Also present as secondary',
  researcherRevealNotActivatedLabel: 'Not activated in this set',

  researcherContrastQuestion:
    "What's different about how responsibility is handled here, compared to your own technology?",

  researcherReflectionFullMatchesDominant:
    'Your top-ranked prediction matched the dominant pattern across this comparison set. Which secondary pattern would you look at next in a similar project, and why?',
  researcherReflectionFullDoesNotMatch:
    'Your top-ranked prediction did not match the dominant pattern across this comparison set. What led you to expect a different pattern? Which case in the comparison set would you revisit first?',
  researcherReflectionZeroPattern:
    'No pattern was dominant across this comparison set — the corpus does not yet offer a clear signal for this combination of domain and function. This is a limit of the current case corpus, not a judgment on your work.',
  researcherReflectionBoundaryExit:
    "Your description could not be mapped to a domain, function, and form within the attempts available. This may mean the framework's current facets do not yet capture this kind of technology — a real limit of the corpus, not something you did wrong.",

  researcherCompleteTitle: 'Session complete',
  researcherCompleteNotYetBody:
    'You have not yet reached the comparison-set reflection in this session.',
  researcherReset: 'Start over',

  researcherSessionMissing: 'No Researcher session is active.',

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
