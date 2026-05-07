<script setup>
import { reactive } from "vue";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(["close", "submit"]);
const form = reactive({ name: "", phone: "", instagram_handle: "" });

function submit() {
  emit("submit", { ...form });
  form.name = "";
  form.phone = "";
  form.instagram_handle = "";
}
</script>

<template>
  <Modal :open="open" title="Add Customer" @close="$emit('close')">
    <div class="space-y-3">
      <Input v-model="form.name" label="Name" />
      <Input v-model="form.phone" label="Phone" />
      <Input v-model="form.instagram_handle" label="Instagram" />
      <div class="flex justify-end">
        <Button @click="submit">Save customer</Button>
      </div>
    </div>
  </Modal>
</template>
