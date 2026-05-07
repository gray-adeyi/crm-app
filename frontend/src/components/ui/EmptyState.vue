<script setup>
defineProps({
  title: { type: String, default: "No data yet" },
  description: { type: String, default: "Create your first record to get started." }
});
</script>

<template>
  <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-900">
    <div class="mx-auto mb-4 h-12 w-12 rounded-full bg-brand-100 dark:bg-brand-900/40" />
    <h3 class="text-lg font-semibold">{{ title }}</h3>
    <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ description }}</p>
  </div>
</template>
