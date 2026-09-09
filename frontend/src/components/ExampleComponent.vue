<template>
  <div>
    <p v-if="message" class="text-body1">
      {{ message }}
    </p>
    <p v-else class="text-grey-6">Press the button above to fetch a message from the backend.</p>

    <q-btn
      color="secondary"
      label="Increment counter"
      unelevated
      no-caps
      @click="emit('increment')"
    />
    <span class="q-ml-sm">Counter: {{ counter }}</span>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useExampleStore } from 'stores/example';

defineOptions({
  name: 'ExampleComponent',
});

defineProps<{
  message: string;
}>();

const emit = defineEmits<{
  increment: [];
}>();

const exampleStore = useExampleStore();
const { counter } = storeToRefs(exampleStore);
</script>
