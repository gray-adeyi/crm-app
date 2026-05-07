<script setup>
import EmptyState from "../ui/EmptyState.vue";

defineProps({
  orders: { type: Array, default: () => [] }
});
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <h3 class="mb-4 text-lg font-semibold">Recent Orders</h3>
    <EmptyState v-if="!orders.length" title="No orders yet" description="Recent orders will show here." />
    <div v-else class="space-y-3">
      <div
        v-for="order in orders.slice(0, 5)"
        :key="order.id"
        class="flex items-start justify-between gap-3 rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-800"
      >
        <div>
          <p class="text-sm font-medium">{{ order.product }}</p>
          <p class="text-xs text-slate-600 dark:text-slate-300">{{ order.customer_name || "Customer" }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Status: <span class="font-medium">{{ order.status }}</span>
          </p>
        </div>
        <p class="whitespace-nowrap text-sm font-semibold">₦{{ (order.total_price ?? order.price ?? 0).toLocaleString() }}</p>
      </div>
    </div>
  </div>
</template>
