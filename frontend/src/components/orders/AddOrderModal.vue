<script setup>
import { computed, reactive, watch } from "vue";

import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  customers: { type: Array, default: () => [] },
  products: { type: Array, default: () => [] }
});
const emit = defineEmits(["close", "submit"]);
const form = reactive({
  product_id: "",
  product: "",
  quantity: 1,
  total_price: 0,
  amount_paid: 0,
  customer_id: "",
  fulfillment_type: "delivery",
  delivery_date: "",
  delivery_time: "",
  delivery_address: "",
  delivery_notes: "",
  notes: "",
  payment_method: ""
});

const balancePreview = computed(() => Math.max(0, Number(form.total_price || 0) - Number(form.amount_paid || 0)));
const isDelivery = computed(() => (form.fulfillment_type || "delivery") === "delivery");

const selectedProduct = computed(() =>
  Number(form.product_id) ? (Array.isArray(props.products) ? props.products.find((p) => p.id === Number(form.product_id)) : null) : null
);
const suggestedTotal = computed(() => {
  const unit = Number(selectedProduct.value?.unit_price || 0);
  const qty = Number(form.quantity || 1);
  return Math.max(0, unit * qty);
});

watch(
  () => [form.product_id, form.quantity],
  () => {
    if (!selectedProduct.value) return;
    // only auto-fill if the user hasn't set a price yet
    if (!Number(form.total_price || 0)) {
      form.total_price = suggestedTotal.value;
    }
  }
);

function submit() {
  const ft = form.fulfillment_type || "delivery";
  emit("submit", {
    product_id: form.product_id ? Number(form.product_id) : null,
    product: form.product_id ? null : form.product,
    quantity: Number(form.quantity || 1),
    total_price: Number(form.total_price),
    amount_paid: Number(form.amount_paid),
    customer_id: Number(form.customer_id),
    fulfillment_type: ft,
    delivery_date: ft === "delivery" ? form.delivery_date || null : null,
    delivery_time: ft === "delivery" ? form.delivery_time || null : null,
    delivery_address: ft === "delivery" ? form.delivery_address || null : null,
    delivery_notes: ft === "delivery" ? form.delivery_notes || null : null,
    notes: form.notes || null,
    payment_method: form.payment_method || null
  });
}
</script>

<template>
  <Modal :open="open" title="Add Order" @close="$emit('close')">
    <div class="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl bg-slate-900 p-4">
      <div class="grid gap-4 md:grid-cols-2">
        <label class="block space-y-1.5">
          <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Product (inventory)</span>
          <select
            v-model="form.product_id"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="">Select product (optional)</option>
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} ({{ Number(p.quantity_in_stock || 0) }} in stock)</option>
          </select>
          <p v-if="selectedProduct" class="text-xs text-slate-500 dark:text-slate-400">
            Unit: ₦{{ Number(selectedProduct.unit_price || 0).toLocaleString() }} • Suggested total: ₦{{ suggestedTotal.toLocaleString() }}
          </p>
        </label>

        <Input v-model="form.quantity" label="Quantity" type="number" />
      </div>

      <Input v-if="!form.product_id" v-model="form.product" label="Custom product name" placeholder="If not in inventory" />

      <div class="grid gap-4 md:grid-cols-2">
        <Input v-model="form.total_price" label="Total price (₦)" type="number" />
        <Input v-model="form.amount_paid" label="Amount paid (₦)" type="number" />
      </div>
      <p class="text-xs text-slate-500 dark:text-slate-400">Balance preview: ₦{{ balancePreview.toLocaleString() }} (server recalculates)</p>
      <Input v-model="form.payment_method" label="Payment method" placeholder="Transfer, POS, cash…" />

      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Fulfillment</span>
        <select
          v-model="form.fulfillment_type"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="delivery">Delivery</option>
          <option value="pickup">Pickup</option>
        </select>
      </label>

      <div v-if="isDelivery" class="grid gap-4 md:grid-cols-2">
        <Input v-model="form.delivery_date" label="Delivery date" type="date" />
        <Input v-model="form.delivery_time" label="Delivery time" type="time" />
      </div>

      <label v-if="isDelivery" class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Delivery address</span>
        <textarea
          v-model="form.delivery_address"
          rows="2"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="Street, city, landmarks…"
        />
      </label>

      <label v-if="isDelivery" class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Delivery notes</span>
        <textarea
          v-model="form.delivery_notes"
          rows="2"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="Instructions, rider notes…"
        />
      </label>

      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Notes</span>
        <textarea
          v-model="form.notes"
          rows="3"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="Internal notes"
        />
      </label>
      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Customer</span>
        <select
          v-model="form.customer_id"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="" disabled>Select customer</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.name }}</option>
        </select>
      </label>
      <div class="flex justify-end gap-2 p-3">
        <Button variant="secondary" type="button" @click="$emit('close')">Cancel</Button>
        <Button type="button" @click="submit">Save order</Button>
      </div>
    </div>
  </Modal>
</template>
