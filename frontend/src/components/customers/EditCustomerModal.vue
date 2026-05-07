<script setup>
import { reactive, watch } from "vue";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  customer: { type: Object, default: null }
});

const emit = defineEmits(["close", "submit"]);
const form = reactive({ name: "", phone: "", instagram_handle: "" });

watch(
  () => props.customer,
  (customer) => {
    form.name = customer?.name || "";
    form.phone = customer?.phone || "";
    form.instagram_handle = customer?.instagram_handle || "";
  },
  { immediate: true }
);

function submit() {
  emit("submit", { ...form });
}
</script>

<template>
  <Modal :open="open" title="Edit Customer" @close="$emit('close')">
    <div class="space-y-3">
      <Input v-model="form.name" label="Name" />
      <Input v-model="form.phone" label="Phone" />
      <Input v-model="form.instagram_handle" label="Instagram" />
      <div class="flex justify-end">
        <Button @click="submit">Update customer</Button>
      </div>
    </div>
  </Modal>
</template>
