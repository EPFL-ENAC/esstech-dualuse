import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useExampleStore = defineStore('example', () => {
  const counter = ref(0);

  function increment() {
    counter.value += 1;
  }

  return { counter, increment };
});
