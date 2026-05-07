<script setup>
import EmptyState from "../ui/EmptyState.vue";
import OrderCard from "./OrderCard.vue";

defineProps({
  orders: { type: Array, default: () => [] },
  customers: { type: Array, default: () => [] }
});

defineEmits(["edit", "delete"]);

function customerName(id, customers) {
  return customers.find((customer) => customer.id === id)?.name || "Unknown";
}
</script>

<template>
  <EmptyState v-if="!orders.length" title="No orders yet" description="Create your first order to start tracking revenue." />
  <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <OrderCard
      v-for="order in orders"
      :key="order.id"
      :order="order"
      :customer-name="customerName(order.customer_id, customers)"
      @edit="$emit('edit', $event)"
      @delete="$emit('delete', $event)"
    />
  </div>
</template>
