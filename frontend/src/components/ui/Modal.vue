<script setup>
import Button from "./Button.vue";

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: "" }
});

defineEmits(["close"]);
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" @click.self="$emit('close')">
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-soft dark:bg-slate-900">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold">{{ title }}</h3>
          <Button variant="ghost" @click="$emit('close')">Close</Button>
        </div>
        <slot />
      </div>
    </div>
  </Teleport>
</template>
