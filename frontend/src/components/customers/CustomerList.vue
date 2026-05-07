<script setup>
import CustomerCard from "./CustomerCard.vue";
import EmptyState from "../ui/EmptyState.vue";
defineProps({ customers: { type: Array, default: () => [] } });
defineEmits(["edit", "delete"]);
</script>

<template>
  <EmptyState
    v-if="!customers.length"
    title="No customers found"
    description="Try adding a customer or adjusting your search."
  />
  <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <CustomerCard
      v-for="customer in customers"
      :key="customer.id"
      :customer="customer"
      @edit="$emit('edit', $event)"
      @delete="$emit('delete', $event)"
    />
  </div>
</template>
