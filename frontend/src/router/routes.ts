import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') },
      { path: 'start', component: () => import('pages/RouteChoicePage.vue') },
      { path: 'intake', component: () => import('pages/IntakePage.vue') },
      { path: 'student', component: () => import('pages/StudentSessionPage.vue') },
      {
        path: 'student/encounter',
        component: () => import('pages/StudentEncounterPage.vue'),
      },
      {
        path: 'student/complete',
        component: () => import('pages/StudentCompletePage.vue'),
      },
      {
        path: 'researcher/intake',
        component: () => import('pages/ResearcherIntakePage.vue'),
      },
      {
        path: 'researcher/comparison-set',
        component: () => import('pages/ResearcherComparisonSetPage.vue'),
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
