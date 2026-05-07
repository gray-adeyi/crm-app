<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: 0 }
});
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:shadow-soft dark:bg-slate-900 dark:ring-slate-800">
    <p class="text-sm text-slate-500 dark:text-slate-400">{{ label }}</p>
    <p class="mt-2 text-2xl font-semibold">{{ value }}</p>
  </div>
</template>
