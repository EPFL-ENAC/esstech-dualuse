import { defineRouter } from '#q-app/wrappers';
import { createRouter, createWebHistory } from 'vue-router';
import routes from './routes';

export default defineRouter(function () {
  return createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Set via build.publicPath in quasar.config.ts.
    history: createWebHistory(process.env.VUE_ROUTER_BASE),
  });
});
