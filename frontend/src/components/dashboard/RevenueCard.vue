<script setup>
defineProps({
  /** Sum of captured payments (`amount_paid`) across orders. */
  amount: { type: Number, default: 0 }
});
</script>

<template>
  <div class="rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 p-3 text-white shadow-soft">
    <p class="text-sm text-white/80">Collected Revenue</p>
    <p class="mt-1 text-xs text-white/70">Total payments received</p>
    <p class="mt-2 text-3xl font-semibold">₦{{ Number(amount || 0).toLocaleString() }}</p>
  </div>
</template>
