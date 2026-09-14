export default {
  appTitle: 'esstech-dualuse',

  goHome: "Retour à l'accueil",
  notFoundMessage: 'Désolé, il n’y a rien ici...',

  welcome: 'Bienvenue sur le boilerplate',
  welcomeHint: 'Ceci est la page d’accueil factice. Remplacez-la par votre contenu réel.',
  fetchMessage: 'Récupérer le message du backend',

  sessionStart: 'Démarrer une session',
  studentOpenDev: 'Accès direct au parcours étudiant (dev)',

  routeChoiceTitle: 'Choisissez votre parcours',
  routeChoiceIntro: 'Sélectionnez l’option qui correspond à ce que vous souhaitez faire.',
  routeChoiceResearcherLabel: 'Parcours chercheur — individuel',
  routeChoiceResearcherHint:
    'Décrivez une technologie, précisez sa fonction et sa forme, puis comparez votre prédiction à des cas similaires.',
  routeChoiceStudentAction: 'Continuer en tant qu’étudiant',
  routeChoiceResearcherAction: 'Continuer en tant que chercheur',
  routeChoiceStarting: 'Démarrage...',

  researcherIntakeTitle: 'Prise en compte de la technologie',

  researcherDescriptionIntro:
    'Décrivez, avec vos propres mots, la technologie sur laquelle vous travaillez.',
  researcherDescriptionHint:
    'Quelques phrases sur ce qu’elle fait et comment elle fonctionne suffisent pour commencer.',
  researcherDescriptionLabel: 'Description',
  researcherDescriptionSubmit: 'Continuer',
  researcherDescriptionSubmitting: 'Enregistrement...',

  researcherTagTitle: 'Cartographiez votre technologie',
  researcherTagIntro:
    'Le domaine, la fonction et la forme situent ensemble votre technologie dans le corpus de cas.',
  researcherTagDomainLabel: 'Domaine',
  researcherTagFunctionsLabel: 'Fonction(s)',
  researcherTagFormsLabel: 'Forme(s)',
  researcherTagSubmit: 'Envoyer',
  researcherTagSubmitting: 'Enregistrement...',
  researcherTagPartialNotice:
    'Le domaine, la fonction et la forme ne sont pas encore tous renseignés. Complétez ce qui manque et envoyez à nouveau.',
  researcherTagAttemptRemaining: 'Une tentative restante.',
  researcherTagRetry: 'Réessayer',
  researcherTagMappedTitle: 'Technologie cartographiée',
  researcherTagMappedBody: 'Le domaine, la fonction et la forme sont tous renseignés.',
  researcherTagContinue: 'Continuer',
  researcherTagExhaustedTitle: 'La cartographie n’a pas pu être complétée',
  researcherTagExhaustedBody:
    'Le domaine, la fonction et la forme n’ont pas pu être confirmés dans les tentatives disponibles. L’outil n’invente pas de correspondance là où la description n’en donne pas.',

  researcherGateTitle: 'Gate et responsabilité',
  researcherGateIntro:
    'Une dernière réflexion avant de comparer votre prédiction à des cas similaires.',
  researcherGateQuestion:
    'Sur quel gate repose principalement le risque de double usage de cette technologie ?',
  researcherGatePostureHint:
    'Au-delà de l’usage que vous envisagez, qui d’autre pourrait utiliser cette technologie ?',
  researcherGateSubmit: 'Continuer',
  researcherGateSubmitting: 'Enregistrement...',
  researcherGateDoneTitle: 'Enregistré',
  researcherGateDoneBody: 'Votre gate et votre réflexion sont enregistrés.',

  researcherComparisonSetTitle: 'Ensemble de comparaison',
  researcherComparisonSetPlaceholderNotice:
    'Espace réservé temporaire — cet écran n’a pas encore été développé. Il confirme seulement que votre gate et votre réflexion ont bien été enregistrés.',
  researcherComparisonSetGateLabel: 'Gate',

  researcherSessionMissing: 'Aucune session chercheur active.',

  intakeTitle: 'Avant de commencer',
  intakeIntro: 'Quelques questions rapides pour préparer votre session.',
  intakeDiagnosticTitle: 'Trois questions rapides',
  intakeComprehensionTitle: 'Une dernière vérification',
  intakeOneAttempt: 'Une seule tentative — la question ne sera pas reposée.',
  intakeSubmit: 'Continuer',
  intakeSubmitting: 'Enregistrement...',
  intakePrimerContinue: 'Compris, continuer',
  intakeContinue: 'Continuer',
  intakeDoneTitle: 'Vous êtes prêt',
  intakeDoneBody: 'Votre session est prête. Choisissez maintenant un cas à traiter.',
  intakeGoToCases: 'Choisir un cas',

  studentTitle: 'Parcours étudiant — individuel',
  studentIntro: 'Traitez jusqu’à trois cas, une décision à la fois.',
  studentStart: 'Démarrer une session',
  studentStarting: 'Démarrage de la session...',
  studentSessionActive: 'Session en cours',
  studentReset: 'Recommencer',

  casesTitle: 'Choisissez un cas',
  casesLoading: 'Chargement des cas...',
  casesEmpty: 'Aucun cas restant. Vous avez traité tous les cas disponibles.',
  caseSelect: 'Travailler sur ce cas',
  caseSelecting: 'Ouverture du cas...',
  confirmSelectTitle: 'Commencer ce cas ?',
  confirmSelectBody:
    'En ouvrant « {title} », vous utilisez l’un des trois cas de cette session. Cette action est irréversible.',
  confirmSelect: 'Commencer ce cas',
  confirmCancel: 'Annuler',

  encounterTitle: 'La situation',
  encounterMissing: 'Aucun cas ouvert. Choisissez-en un pour continuer.',
  encounterStep: 'Cas {current} sur {total}',

  framingTitle: 'Avant de vous engager',
  framingHint:
    'Répondez avec vos propres mots. Vos réponses sont enregistrées avec votre engagement.',

  commitmentTitle: 'Votre lecture',
  commitmentPattern: 'Pattern',
  commitmentGate: 'Gate',
  commitmentHint:
    'Choisissez le pattern et le gate qui, selon vous, sont déterminants dans ce cas.',
  commitmentSubmit: 'S’engager',
  commitmentSubmitting: 'Enregistrement de votre engagement...',
  commitmentSaved: 'Engagement enregistré. Vous pouvez révéler le cas.',
  commitmentIncomplete: 'Choisissez d’abord un pattern et un gate.',

  revealAction: 'Révéler le cas',
  revealLoading: 'Révélation du cas...',
  revealTitle: 'Ce qui s’est passé',
  revealYourReading: 'Votre lecture',
  revealMainPath: 'Chemin principal',
  revealSources: 'Sources',
  revealAt: 'Révélé le {at}',
  revealAgain: 'Afficher à nouveau',

  contrastContinue: 'Continuer',
  contrastTwinTitle: 'Un cas-jumeau existe',
  contrastWhoQuestion:
    'Qui portait la responsabilité dans ce cas-jumeau, et en quoi cela diffère-t-il du cas que vous venez de lire ?',
  contrastResponseLabel: 'Votre réflexion',
  contrastSubmit: 'Envoyer',
  contrastSubmitting: 'Enregistrement...',
  contrastSaved: 'Réflexion enregistrée.',
  contrastOpenAreaMessage:
    "Ce cas de figure n'est pas encore couvert par un cas-jumeau dans le corpus actuel. L'outil n'invente pas de solution là où la base de preuves n'en a pas.",

  anotherCaseProgress: 'Vous avez travaillé {current} cas sur {total}.',
  anotherCaseYes: 'Oui, un autre cas',
  anotherCaseNo: 'Non',
  anotherCaseFinish: 'Terminer',

  completeTitle: 'Votre bilan de session',
  completeBody: 'Un résumé de vos réflexions de cas pour cette session.',
  completeGoHome: "Retour à l'accueil",
  completeNoCasesBody: "Vous n'avez pas encore terminé de réflexion de cas dans cette session.",
  completeCasesExploredLabel: 'Cas explorés',
  completeDecisionPointsLabel: 'Gates examinés',
  completePatternsSelectedLabel: 'Patterns sélectionnés',
  completeMatchBreakdownLabel: 'Répartition des correspondances',
  completeCounterCaseReflectionsLabel: 'Réflexions sur les cas-jumeaux complétées',
  completeSuggestedFocusLabel: 'Prochain point à explorer',

  scaffoldingLabel: "Niveau d'accompagnement",
  scaffoldingPlaceholderNote:
    'Indication provisoire et non validée : elle ne constitue pas une évaluation de votre compréhension.',
  scaffoldingHigh: 'Accompagnement renforcé requis',
  scaffoldingStandard: 'Accompagnement standard requis',
  scaffoldingLow: 'Accompagnement léger requis',

  matchMatch: 'Correspondance complète',
  matchPartial: 'Correspondance partielle',
  matchMismatch: 'Aucune correspondance',
  matchMatchHint: 'Vous avez identifié à la fois le pattern et le gate.',
  matchPartialHint: 'Vous avez identifié l’un des deux.',
  matchMismatchHint: 'Aucun des deux ne correspond au chemin principal du cas.',

  reflectionMatch:
    'Vous avez identifié {pattern} à {gate}. Votre lecture correspond au chemin principal du cas. Quel autre pattern ou gate examineriez-vous ensuite, et pourquoi ?',
  reflectionPartialMatch:
    "Vous avez identifié {pattern} à {gate}. Votre lecture correspond au chemin principal du cas pour l'un des deux éléments seulement. Lequel avez-vous correctement identifié — le pattern ou le gate — et qu'est-ce qui vous a induit en erreur sur l'autre ?",
  reflectionMismatch:
    'Vous avez identifié {pattern} à {gate}. Votre lecture diffère du chemin principal du cas sur les deux éléments. Quelle hypothèse a guidé votre choix ? Quelle partie des éléments du cas reverriez-vous ?',

  errorTitle: 'Une erreur est survenue',
  errorRetry: 'Réessayer',
  errorUnexpected: 'Erreur inattendue. Veuillez réessayer.',
  errorNotYours: 'Ce contenu n’est plus disponible. Démarrez une nouvelle session pour continuer.',
};
