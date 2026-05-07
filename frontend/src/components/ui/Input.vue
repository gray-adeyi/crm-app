<script setup>
defineProps({
  modelValue: { type: [String, Number], default: "" },
  label: { type: String, default: "" },
  type: { type: String, default: "text" },
  placeholder: { type: String, default: "" },
  error: { type: String, default: "" }
});

defineEmits(["update:modelValue"]);
</script>

<template>
  <label class="block space-y-1.5">
    <span v-if="label" class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ label }}</span>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-900 dark:focus:ring-brand-900"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <p v-if="error" class="text-xs text-rose-600">{{ error }}</p>
  </label>
</template>
