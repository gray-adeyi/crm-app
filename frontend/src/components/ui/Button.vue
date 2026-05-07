<script setup>
const props = defineProps({
  variant: { type: String, default: "primary" },
  type: { type: String, default: "button" },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false }
});

const classesByVariant = {
  primary: "bg-brand-600 text-white hover:bg-brand-700",
  secondary: "bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50",
  danger: "bg-rose-600 text-white hover:bg-rose-700",
  ghost: "bg-transparent text-slate-600 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
};
</script>

<template>
  <button
    :type="props.type"
    :disabled="props.disabled"
    class="inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium transition-all disabled:cursor-not-allowed disabled:opacity-50"
    :class="[classesByVariant[props.variant], props.block ? 'w-full' : '']"
  >
    <slot />
  </button>
</template>
