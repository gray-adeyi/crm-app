<script setup>
import { computed, reactive, watch } from "vue";

import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Modal from "../ui/Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  order: { type: Object, default: null },
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
  status: "pending",
  fulfillment_type: "delivery",
  delivery_date: "",
  delivery_time: "",
  delivery_address: "",
  delivery_notes: "",
  notes: "",
  payment_method: ""
});

watch(
  () => props.order,
  (order) => {
    form.product = order?.product || "";
    form.product_id = order?.product_id || "";
    form.quantity = order?.quantity || 1;
    form.total_price = order?.total_price ?? order?.price ?? 0;
    form.amount_paid = order?.amount_paid || 0;
    form.customer_id = order?.customer_id || "";
    form.status = order?.status || "pending";
    form.fulfillment_type = order?.fulfillment_type || "delivery";
    form.delivery_date = order?.delivery_date || "";
    form.delivery_time = order?.delivery_time || "";
    form.delivery_address = order?.delivery_address || "";
    form.delivery_notes = order?.delivery_notes || "";
    form.notes = order?.notes || "";
    form.payment_method = order?.payment_method || "";
  },
  { immediate: true }
);

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
    status: form.status,
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
  <Modal :open="open" title="Edit Order" @close="$emit('close')">
    <div class="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-4 ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800">
      <div class="grid gap-4 md:grid-cols-2">
        <label class="block space-y-1.5">
          <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Product (inventory)</span>
          <select
            v-model="form.product_id"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="">Select product (optional)</option>
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <p v-if="selectedProduct" class="text-xs text-slate-500 dark:text-slate-400">
            Unit: ₦{{ Number(selectedProduct.unit_price || 0).toLocaleString() }} • Suggested total: ₦{{ suggestedTotal.toLocaleString() }}
          </p>
        </label>

        <Input v-model="form.quantity" label="Quantity" type="number" />
      </div>

      <Input v-if="!form.product_id" v-model="form.product" label="Custom product name" />

      <div class="grid gap-4 md:grid-cols-2">
        <Input v-model="form.total_price" label="Total price (₦)" type="number" />
        <Input v-model="form.amount_paid" label="Amount paid (₦)" type="number" />
      </div>
      <p class="text-xs text-slate-500 dark:text-slate-400">Balance preview: ₦{{ balancePreview.toLocaleString() }}</p>
      <Input v-model="form.payment_method" label="Payment method" />

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
        />
      </label>

      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Notes</span>
        <textarea
          v-model="form.notes"
          rows="3"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
      </label>
      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Customer</span>
        <select
          v-model="form.customer_id"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.name }}</option>
        </select>
      </label>
      <label class="block space-y-1.5">
        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Status</span>
        <select
          v-model="form.status"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="pending">pending</option>
          <option value="partial">partial</option>
          <option value="paid">paid</option>
          <option value="delivered">delivered</option>
          <option value="cancelled">cancelled</option>
        </select>
      </label>
      <p class="text-xs text-slate-500 dark:text-slate-400">
        Payment status auto-updates from amounts unless you choose <strong>delivered</strong> or <strong>cancelled</strong>.
      </p>
      <div class="flex justify-end gap-2 pt-3">
        <Button variant="secondary" type="button" @click="$emit('close')">Cancel</Button>
        <Button type="button" @click="submit">Update order</Button>
      </div>
    </div>
  </Modal>
</template>
