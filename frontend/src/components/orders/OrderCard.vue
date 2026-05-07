<script setup>
import { getActivePinia } from "pinia";

import Button from "../ui/Button.vue";
import { useSessionStore } from "../../stores/session";
import { downloadOrderInvoice, downloadOrderReceipt } from "../../utils/documents";

const props = defineProps({
  order: { type: Object, required: true },
  customerName: { type: String, default: "Unknown" }
});

defineEmits(["edit", "delete"]);

const badge = {
  pending: "bg-amber-100 text-amber-700",
  partial: "bg-sky-100 text-sky-700",
  paid: "bg-emerald-100 text-emerald-700",
  delivered: "bg-violet-100 text-violet-700",
  cancelled: "bg-slate-100 text-slate-600"
};

function total() {
  return Number(props.order.total_price ?? props.order.price ?? 0);
}

function currentUser() {
  const pinia = getActivePinia();
  return pinia ? useSessionStore(pinia).user : null;
}

function pdfInvoice() {
  downloadOrderInvoice(props.order, props.customerName, currentUser());
}

function pdfReceipt() {
  downloadOrderReceipt(props.order, props.customerName, currentUser());
}

function printInvoice() {
  const tp = total();
  const biz = currentUser()?.business_name || "Invoice";
  const w = window.open("", "_blank");
  if (!w) return;
  const html = `<!doctype html><html><head><title>Invoice</title></head><body style="font-family:system-ui;padding:24px;">
    <h1>${biz}</h1>
    <p>Invoice #${props.order.id}</p>
    <p>Customer: ${props.customerName}</p>
    <p>Product: ${props.order.product}</p>
    <p>Total: ₦${tp.toLocaleString()}</p>
    <p>Paid: ₦${Number(props.order.amount_paid || 0).toLocaleString()}</p>
    <p>Balance: ₦${Number(props.order.balance || 0).toLocaleString()}</p>
    <p>Status: ${props.order.status}</p>
  </body></html>`;
  w.document.write(html);
  w.document.close();
  w.focus();
  w.print();
}
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <div class="flex items-start justify-between">
      <div>
        <p class="font-semibold">{{ order.product }}</p>
        <p class="text-sm text-slate-500">{{ customerName }}</p>
        <p v-if="order.fulfillment_type" class="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">
          {{ order.fulfillment_type === "pickup" ? "Pickup" : "Delivery" }}
        </p>
      </div>
      <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="badge[order.status] || badge.pending">
        {{ order.status }}
      </span>
    </div>
    <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
      <div><p class="text-slate-500">Total</p><p class="font-medium">₦{{ total().toLocaleString() }}</p></div>
      <div><p class="text-slate-500">Paid</p><p class="font-medium">₦{{ Number(order.amount_paid || 0).toLocaleString() }}</p></div>
      <div><p class="text-slate-500">Balance</p><p class="font-medium">₦{{ Number(order.balance || 0).toLocaleString() }}</p></div>
    </div>
    <div class="mt-4 flex flex-wrap gap-2">
      <Button variant="secondary" @click="$emit('edit', order)">Edit</Button>
      <Button variant="ghost" @click="pdfInvoice">Invoice PDF</Button>
      <Button variant="ghost" @click="pdfReceipt">Receipt PDF</Button>
      <Button variant="ghost" @click="printInvoice">Print</Button>
      <Button variant="danger" @click="$emit('delete', order)">Delete</Button>
    </div>
  </div>
</template>
