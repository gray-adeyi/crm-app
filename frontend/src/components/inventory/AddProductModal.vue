<script setup>
import { reactive } from "vue";

import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(["close", "submit"]);

const form = reactive({
  name: "",
  sku: "",
  category: "",
  unit_price: 0,
  quantity_in_stock: 0,
  reorder_threshold: 0,
  image: "",
  description: ""
});

function submit() {
  emit("submit", {
    name: form.name,
    sku: form.sku || null,
    category: form.category || null,
    unit_price: Number(form.unit_price || 0),
    quantity_in_stock: Number(form.quantity_in_stock || 0),
    reorder_threshold: Number(form.reorder_threshold || 0),
    image: form.image || null,
    description: form.description || null
  });
}
</script>

<template>
  <Modal :open="open" title="Add Inventory Item" @close="$emit('close')">
    <div class="grid gap-4 md:grid-cols-2">
      <Input v-model="form.name" label="Product name" placeholder="Gucci Bag" />
      <Input v-model="form.sku" label="SKU (optional)" placeholder="GB-0001" />
      <Input v-model="form.category" label="Category" placeholder="Bags" />
      <Input v-model="form.unit_price" label="Unit price (₦)" type="number" />
      <Input v-model="form.quantity_in_stock" label="Quantity in stock" type="number" />
      <Input v-model="form.reorder_threshold" label="Reorder threshold" type="number" />
      <div class="md:col-span-2">
        <Input v-model="form.image" label="Image URL (optional)" placeholder="https://..." />
      </div>
      <label class="md:col-span-2 block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Description</span>
        <textarea
          v-model="form.description"
          rows="3"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="Short description for your team"
        />
      </label>
    </div>

    <div class="mt-5 flex justify-end gap-2">
      <Button variant="secondary" type="button" @click="$emit('close')">Cancel</Button>
      <Button type="button" @click="submit">Save</Button>
    </div>
  </Modal>
</template>

