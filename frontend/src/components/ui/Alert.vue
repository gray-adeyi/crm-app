<script setup>
defineProps({
  type: { type: String, default: "success" },
  message: { type: String, default: "" }
});

const classByType = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-300",
  error: "bg-rose-50 text-rose-700 ring-rose-300",
  info: "bg-sky-50 text-sky-700 ring-sky-300"
};
</script>

<template>
  <div v-if="message" class="rounded-xl px-4 py-3 text-sm ring-1" :class="classByType[type]">
    {{ message }}
  </div>
</template>
