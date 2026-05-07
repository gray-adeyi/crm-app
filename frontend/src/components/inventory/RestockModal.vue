<script setup>
import { computed, reactive, watch } from "vue";

import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  item: { type: Object, default: null }
});
const emit = defineEmits(["close", "submit"]);

const form = reactive({ quantity: 1, reason: "" });
const title = computed(() => (props.item ? `Restock — ${props.item.name}` : "Restock"));

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    form.quantity = 1;
    form.reason = "";
  }
);

function submit() {
  emit("submit", { quantity: Number(form.quantity || 1), reason: form.reason || null });
}
</script>

<template>
  <Modal :open="open" :title="title" @close="$emit('close')">
    <div class="space-y-3">
      <Input v-model="form.quantity" label="Add quantity" type="number" />
      <Input v-model="form.reason" label="Reason (optional)" placeholder="Supplier restock, adjustment..." />
      <p v-if="item" class="text-xs text-slate-500 dark:text-slate-400">
        Current stock: {{ Number(item.quantity_in_stock || 0).toLocaleString() }}
      </p>
    </div>

    <div class="mt-5 flex justify-end gap-2">
      <Button variant="secondary" type="button" @click="$emit('close')">Cancel</Button>
      <Button type="button" @click="submit">Restock</Button>
    </div>
  </Modal>
</template>

