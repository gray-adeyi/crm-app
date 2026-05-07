<script setup>
import { reactive, watch } from "vue";

import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  item: { type: Object, default: null }
});
const emit = defineEmits(["close", "submit"]);

const form = reactive({
  name: "",
  sku: "",
  category: "",
  unit_price: 0,
  reorder_threshold: 0,
  image: "",
  description: ""
});

watch(
  () => props.item,
  (item) => {
    if (!item) return;
    form.name = item.name || "";
    form.sku = item.sku || "";
    form.category = item.category || "";
    form.unit_price = Number(item.unit_price || 0);
    form.reorder_threshold = Number(item.reorder_threshold || 0);
    form.image = item.image || "";
    form.description = item.description || "";
  },
  { immediate: true }
);

function submit() {
  emit("submit", {
    name: form.name,
    sku: form.sku || null,
    category: form.category || null,
    unit_price: Number(form.unit_price || 0),
    reorder_threshold: Number(form.reorder_threshold || 0),
    image: form.image || null,
    description: form.description || null
  });
}
</script>

<template>
  <Modal :open="open" title="Edit Inventory Item" @close="$emit('close')">
    <div class="grid gap-4 md:grid-cols-2">
      <Input v-model="form.name" label="Product name" />
      <Input v-model="form.sku" label="SKU (optional)" />
      <Input v-model="form.category" label="Category" />
      <Input v-model="form.unit_price" label="Unit price (₦)" type="number" />
      <Input v-model="form.reorder_threshold" label="Reorder threshold" type="number" />
      <div class="md:col-span-2">
        <Input v-model="form.image" label="Image URL (optional)" />
      </div>
      <label class="md:col-span-2 block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Description</span>
        <textarea
          v-model="form.description"
          rows="3"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
      </label>
    </div>

    <div class="mt-5 flex justify-end gap-2">
      <Button variant="secondary" type="button" @click="$emit('close')">Cancel</Button>
      <Button type="button" @click="submit">Save changes</Button>
    </div>
  </Modal>
</template>

