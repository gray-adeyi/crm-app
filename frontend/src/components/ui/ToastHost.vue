<script setup>
import { useToast } from "../../composables/useToast";

const { toasts, remove } = useToast();

const styles = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-100",
  error: "border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-100",
  info: "border-slate-200 bg-white text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
};
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-end gap-2 p-4 sm:p-6">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="pointer-events-auto w-full max-w-sm rounded-xl border px-4 py-3 shadow-lg ring-1 ring-black/5 dark:ring-white/10"
      :class="styles[t.type] || styles.info"
    >
      <div class="flex items-start justify-between gap-3">
        <div>
          <p v-if="t.title" class="text-xs font-semibold uppercase tracking-wide opacity-70">{{ t.title }}</p>
          <p class="text-sm font-medium">{{ t.message }}</p>
        </div>
        <button type="button" class="text-xs opacity-60 hover:opacity-100" @click="remove(t.id)">✕</button>
      </div>
    </div>
  </div>
</template>
