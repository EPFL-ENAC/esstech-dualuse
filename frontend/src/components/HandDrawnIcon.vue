<template>
  <svg class="hand-icon" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <g stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <template v-if="name === 'arrow'">
        <path d="M4 17c8-.8 14-.4 23-1" />
        <path d="m21 10 6 6-5.4 6.5" />
      </template>
      <template v-else-if="name === 'clock'">
        <path
          d="M16 3.5c8 .2 12.5 5.6 12.2 12.8-.3 7.5-5.1 12-12.7 12C8.2 28.2 3.7 23.5 3.8 16 4 8.4 8.6 3.4 16 3.5Z"
        />
        <path d="M15.7 8.5v8.2l5.5 3.2" />
      </template>
      <template v-else-if="name === 'shield'">
        <path
          d="M16 3.5c3 2.2 6.5 3.2 10.3 3.5-.1 10.4-2.8 17-10.2 21.2C8.8 24.4 5.7 17.7 5.8 7 9.7 6.7 13 5.6 16 3.5Z"
        />
        <path d="m10.8 15.8 3.2 3.4 7.2-7" />
      </template>
      <template v-else-if="name === 'thought'">
        <path
          d="M8.2 20.8c-2.8-1.8-4.1-4.4-3.5-7.5.8-4.5 5-7.6 10.4-7.7 6.5 0 11.5 3.8 11.6 9.1.1 4.7-4.2 8.5-10.2 8.8-1.8.1-3.5-.2-5-.7L7.4 26l.8-5.2Z"
        />
        <path d="M11 13.5c1.3-2.2 4-3.2 6.2-2.1 2.7 1.3 2.5 4.3.3 5.6-.8.5-1.3 1.1-1.3 2" />
        <path d="M16 21.7h.1" />
      </template>
      <template v-else-if="name === 'student'">
        <path d="m3.5 12.3 12.4-6 12.6 6.2-12.3 6.2-12.7-6.4Z" />
        <path d="M8 15.2v7.2c5.1 3.1 10.6 3.3 16-.2v-7" />
        <path d="M28.5 12.5v8" />
      </template>
      <template v-else-if="name === 'research'">
        <path d="M12 4.2h8M14 4.5v7.2l-7 11.7c-.9 1.6 0 3.4 2 3.4h14c2 0 3-1.9 2-3.5l-7-11.6V4.5" />
        <path d="M10.2 20.4c3.1-1.2 4.9 1.3 7.7.1 2.1-.9 3.7.3 5.6 1.5" />
        <path d="M14.2 16h.1M19 14h.1" />
      </template>
      <template v-else-if="name === 'explore'">
        <path
          d="M13.8 5C8 5.7 4.4 9.8 4.7 15.7c.3 6.7 5.3 10.7 11.8 10.3 5.7-.3 9.5-4.1 9.7-9.7.2-6-3.7-10-9.4-10.9"
        />
        <path d="m20.5 11-2.8 6.2-6.4 3 2.9-6.4 6.3-2.8Z" />
        <path d="m23.2 23.3 5 5" />
      </template>
      <template v-else-if="name === 'branch'">
        <path d="M6 5.5v20M6 11c7 0 10 1 10 6v8" />
        <path d="m12 21 4 4 4-4M3 6h6M13 6h6M22 6h7" />
      </template>
      <template v-else>
        <path
          d="M16 3.8c-6.2 0-10.4 4.2-10.1 9.7.2 3.5 2.2 5.6 4.8 7.7 1.2 1 1.8 2.1 1.9 3.5h7c.1-1.5.8-2.7 2-3.7 2.7-2 4.5-4.4 4.4-7.7-.2-5.5-4.3-9.5-10-9.5Z"
        />
        <path d="M12.5 28h7M13 24.8h6" />
        <path d="M15.8 8.5c-2.8.4-4.4 2.2-4.5 4.8" />
      </template>
    </g>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<style scoped>
.hand-icon {
  display: block;
  width: 1.5em;
  height: 1.5em;
  overflow: visible;
}
</style>
