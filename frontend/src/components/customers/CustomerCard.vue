<script setup>
import Button from "../ui/Button.vue";
defineProps({ customer: { type: Object, required: true } });
defineEmits(["edit", "delete"]);
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <p class="text-base font-semibold">{{ customer.name }}</p>
    <p class="mt-1 text-sm text-slate-500">{{ customer.phone }}</p>
    <p class="text-sm text-slate-500">{{ customer.instagram_handle || "No Instagram" }}</p>
    <div class="mt-4 flex gap-2">
      <Button variant="secondary" @click="$emit('edit', customer)">Edit</Button>
      <Button variant="danger" @click="$emit('delete', customer)">Delete</Button>
    </div>
  </div>
</template>
