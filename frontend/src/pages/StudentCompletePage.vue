<template>
  <q-page class="q-pa-md">
    <div class="complete-page column q-gutter-md">
      <q-banner class="bg-amber-1 text-amber-10" rounded dense>
        <template #avatar><q-icon name="science" color="amber-8" /></template>
        {{ t('completePlaceholderNotice') }}
      </q-banner>

      <q-card flat bordered>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">{{ t('completeTitle') }}</div>
          <div class="text-body1">{{ t('completeBody') }}</div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            color="primary"
            unelevated
            :label="t('completeGoHome')"
            @click="router.push('/')"
          />
        </q-card-actions>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

defineOptions({
  name: 'StudentCompletePage',
});

const { t } = useI18n();
const router = useRouter();
</script>

<style scoped>
.complete-page {
  max-width: 760px;
  margin: 0 auto;
}
</style>
