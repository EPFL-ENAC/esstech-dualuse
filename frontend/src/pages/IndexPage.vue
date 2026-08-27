<template>
  <q-page class="q-pa-md row items-start content-start">
    <q-card class="q-mx-auto" style="min-width: 420px">
      <q-card-section>
        <div class="text-h5">{{ t('welcome') }}</div>
        <div class="text-subtitle2 text-grey-7 q-mt-xs">{{ t('welcomeHint') }}</div>
      </q-card-section>

      <q-card-section>
        <ExampleComponent :message="message" @increment="increment" />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn color="primary" :label="t('fetchMessage')" unelevated @click="fetchMessage" />
      </q-card-actions>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiFetch } from 'boot/api';
import ExampleComponent from 'components/ExampleComponent.vue';
import { useExampleStore } from 'stores/example';

defineOptions({
  name: 'IndexPage',
});

const { t } = useI18n();
const exampleStore = useExampleStore();
const message = ref('');

function increment() {
  exampleStore.increment();
}

async function fetchMessage() {
  const data = await apiFetch<{ message: string }>('/dummy');
  message.value = data.message;
}
</script>
