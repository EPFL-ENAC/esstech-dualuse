import { defineStore } from '#q-app/wrappers';
import { createPinia } from 'pinia';
import persist from 'pinia-plugin-persistedstate';

export default defineStore(() => {
  const pinia = createPinia();

  pinia.use(persist);

  return pinia;
});
