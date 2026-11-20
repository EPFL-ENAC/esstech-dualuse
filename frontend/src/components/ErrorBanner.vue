<template>
  <q-banner class="app-alert--danger">
    <template #avatar><q-icon name="warning" color="negative" /></template>
    <div class="text-weight-medium">{{ t('errorTitle') }}</div>
    <div>{{ message }}</div>
    <template v-if="$slots.action" #action>
      <slot name="action" />
    </template>
  </q-banner>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineOptions({ name: 'ErrorBanner' });

defineProps<{ message: string }>();
defineSlots<{ action?: () => unknown }>();

const { t } = useI18n();
</script>
