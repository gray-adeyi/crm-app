<script setup>
defineProps({
  upcoming: { type: Array, default: () => [] },
  today: { type: Array, default: () => [] },
  overdue: { type: Array, default: () => [] },
  pickups: { type: Array, default: () => [] },
  completed: { type: Array, default: () => [] }
});

function formatRow(row) {
  const date = row.delivery_date ? row.delivery_date : "—";
  const time = row.delivery_time ? row.delivery_time : "—";
  return `${date} • ${time}`;
}
</script>

<template>
  <div class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
    <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold">Today’s deliveries</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">What needs attention today.</p>
        </div>
        <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {{ today.length }}
        </span>
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="d in today" :key="d.id" class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ d.customer_name || "Customer" }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ d.product }} • Qty {{ d.quantity }}</p>
          </div>
          <p class="shrink-0 text-xs text-slate-500 dark:text-slate-400">{{ formatRow(d) }}</p>
        </li>
        <li v-if="!today.length" class="text-sm text-slate-500 dark:text-slate-400">No deliveries scheduled for today.</li>
      </ul>
    </div>

    <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold">Upcoming deliveries</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Next 7 days.</p>
        </div>
        <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {{ upcoming.length }}
        </span>
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="d in upcoming" :key="d.id" class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ d.customer_name || "Customer" }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ d.product }} • Qty {{ d.quantity }}</p>
          </div>
          <p class="shrink-0 text-xs text-slate-500 dark:text-slate-400">{{ formatRow(d) }}</p>
        </li>
        <li v-if="!upcoming.length" class="text-sm text-slate-500 dark:text-slate-400">Nothing scheduled yet.</li>
      </ul>
    </div>

    <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold">Overdue deliveries</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Past delivery dates not marked delivered.</p>
        </div>
        <span
          class="rounded-full px-2.5 py-1 text-xs font-semibold"
          :class="
            overdue.length
              ? 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-200'
              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
          "
        >
          {{ overdue.length }}
        </span>
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="d in overdue" :key="d.id" class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ d.customer_name || "Customer" }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ d.product }} • Qty {{ d.quantity }}</p>
          </div>
          <p class="shrink-0 text-xs text-slate-500 dark:text-slate-400">{{ formatRow(d) }}</p>
        </li>
        <li v-if="!overdue.length" class="text-sm text-slate-500 dark:text-slate-400">No overdue deliveries.</li>
      </ul>
    </div>
  </div>

  <div class="grid gap-4 lg:grid-cols-2">
    <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold">Pickups ready</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Orders scheduled for customer collection.</p>
        </div>
        <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {{ pickups.length }}
        </span>
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="d in pickups" :key="d.id" class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ d.customer_name || "Customer" }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ d.product }} • Qty {{ d.quantity }}</p>
          </div>
          <p class="shrink-0 text-xs font-medium text-indigo-600 dark:text-indigo-300">Pickup</p>
        </li>
        <li v-if="!pickups.length" class="text-sm text-slate-500 dark:text-slate-400">No pickup orders waiting.</li>
      </ul>
    </div>

    <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold">Completed deliveries</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Recently marked as delivered.</p>
        </div>
        <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200">
          {{ completed.length }}
        </span>
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="d in completed" :key="d.id" class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ d.customer_name || "Customer" }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ d.product }} • Qty {{ d.quantity }}</p>
          </div>
          <p class="shrink-0 text-xs text-slate-500 dark:text-slate-400">{{ formatRow(d) }}</p>
        </li>
        <li v-if="!completed.length" class="text-sm text-slate-500 dark:text-slate-400">No completed deliveries yet.</li>
      </ul>
    </div>
  </div>
</template>

