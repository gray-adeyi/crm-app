<script setup>
import Button from "../ui/Button.vue";

defineProps({
  items: { type: Array, default: () => [] }
});
defineEmits(["edit", "restock", "delete"]);

function badgeFor(item) {
  const qty = Number(item.quantity_in_stock || 0);
  if (qty <= 0) return { label: "Out of stock", cls: "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-900/20 dark:text-rose-200 dark:ring-rose-900/40" };
  if (item.reorder_threshold > 0 && qty <= item.reorder_threshold)
    return { label: "Low stock", cls: "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-900/20 dark:text-amber-200 dark:ring-amber-900/40" };
  return { label: "In stock", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-200 dark:ring-emerald-900/40" };
}
</script>

<template>
  <div class="overflow-hidden rounded-2xl bg-white ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
        <thead class="bg-slate-50 dark:bg-slate-900">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Product</th>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">SKU</th>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Category</th>
            <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Unit price</th>
            <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Stock</th>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status</th>
            <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
          <tr v-for="item in items" :key="item.id" class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <div
                  class="h-10 w-10 overflow-hidden rounded-xl bg-slate-100 ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700"
                >
                  <img v-if="item.image" :src="item.image" class="h-full w-full object-cover" />
                </div>
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ item.name }}</p>
                  <p v-if="item.description" class="truncate text-xs text-slate-500 dark:text-slate-400">{{ item.description }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">{{ item.sku || "—" }}</td>
            <td class="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">{{ item.category || "—" }}</td>
            <td class="px-4 py-3 text-right text-sm font-medium text-slate-900 dark:text-white">
              ₦{{ Number(item.unit_price || 0).toLocaleString() }}
            </td>
            <td class="px-4 py-3 text-right text-sm font-medium text-slate-900 dark:text-white">
              {{ Number(item.quantity_in_stock || 0).toLocaleString() }}
            </td>
            <td class="px-4 py-3">
              <span
                class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1"
                :class="badgeFor(item).cls"
              >
                {{ badgeFor(item).label }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="inline-flex flex-wrap justify-end gap-2">
                <Button variant="secondary" size="sm" @click="$emit('restock', item)">Restock</Button>
                <Button variant="secondary" size="sm" @click="$emit('edit', item)">Edit</Button>
                <Button variant="danger" size="sm" @click="$emit('delete', item)">Delete</Button>
              </div>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="7" class="px-4 py-10 text-center text-sm text-slate-500 dark:text-slate-400">
              No inventory items yet. Add your first product to start tracking stock.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

