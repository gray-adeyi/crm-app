<script setup>
defineProps({
  paidCount: { type: Number, default: 0 },
  pendingCount: { type: Number, default: 0 }
});
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <h3 class="mb-4 text-lg font-semibold">Payment Overview</h3>
    <div class="space-y-3">
      <div>
        <div class="mb-1 flex justify-between text-xs text-slate-500">
          <span>Paid</span><span>{{ paidCount }}</span>
        </div>
        <div class="h-2 rounded bg-slate-200 dark:bg-slate-700">
          <div class="h-2 rounded bg-emerald-500" :style="{ width: `${Math.min(paidCount * 10, 100)}%` }" />
        </div>
      </div>
      <div>
        <div class="mb-1 flex justify-between text-xs text-slate-500">
          <span>Pending / Partial</span><span>{{ pendingCount }}</span>
        </div>
        <div class="h-2 rounded bg-slate-200 dark:bg-slate-700">
          <div class="h-2 rounded bg-amber-500" :style="{ width: `${Math.min(pendingCount * 10, 100)}%` }" />
        </div>
      </div>
    </div>
  </div>
</template>
