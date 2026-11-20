<template>
  <q-select
    v-model="model"
    :options="PATTERN_OPTIONS"
    :label="label"
    :disable="disable"
    :clearable="clearable"
    outlined
    emit-value
    map-options
  >
    <template #option="{ itemProps, opt }">
      <q-item v-bind="itemProps">
        <q-item-section>
          <q-item-label>{{ opt.label }}</q-item-label>
          <q-item-label caption class="pattern-select__caption">
            {{ opt.description }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import type { Pattern } from 'src/api/taxonomy';
import { PATTERN_OPTIONS } from 'src/content/patterns';

defineOptions({ name: 'PatternSelect' });

defineProps<{ label: string; disable?: boolean; clearable?: boolean }>();

const model = defineModel<Pattern | null>({ required: true });
</script>

<style scoped>
.pattern-select__caption {
  white-space: normal;
}
</style>
