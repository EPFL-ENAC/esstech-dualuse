export default {
  appTitle: 'esstech-dualuse',

  goHome: "Retour à l'accueil",
  notFoundMessage: 'Désolé, il n’y a rien ici...',

  welcome: 'Bienvenue sur le boilerplate',
  welcomeHint: 'Ceci est la page d’accueil factice. Remplacez-la par votre contenu réel.',
  fetchMessage: 'Récupérer le message du backend',

  sessionStart: 'Démarrer une session',
  studentOpenDev: 'Accès direct au parcours étudiant (dev)',

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
