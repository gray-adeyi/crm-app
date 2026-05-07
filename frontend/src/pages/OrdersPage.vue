<script setup>
import { computed, onMounted, ref } from "vue";

import DashboardLayout from "../components/layout/DashboardLayout.vue";
import AddOrderModal from "../components/orders/AddOrderModal.vue";
import EditOrderModal from "../components/orders/EditOrderModal.vue";
import OrderList from "../components/orders/OrderList.vue";
import Button from "../components/ui/Button.vue";
import Modal from "../components/ui/Modal.vue";
import Spinner from "../components/ui/Spinner.vue";
import { refreshDashboard, useDashboard } from "../composables/useDashboard";
import { useToast } from "../composables/useToast";
import { useCustomers } from "../composables/useCustomers";
import { useInventory } from "../composables/useInventory";
import { useOrders } from "../composables/useOrders";
import { exportOrdersPdf, exportOrdersXlsx, exportRevenueReportPdf } from "../utils/documents";
import { useSessionStore } from "../stores/session";

const { success, error } = useToast();
const { dashboard } = useDashboard();
const { customers, fetchCustomers } = useCustomers();
const { items: products, fetchInventory } = useInventory();
const { orders, loading, fetchOrders, addOrder, updateOrder, deleteOrder } = useOrders();
const session = useSessionStore();
const canBulkExport = computed(() => !!session.user?.can_bulk_export);
const analyticsFull = computed(() => !!session.user?.analytics_full);
const addOpen = ref(false);
const editOpen = ref(false);
const deleteOpen = ref(false);
const selectedOrder = ref(null);

onMounted(async () => {
  await Promise.all([fetchCustomers(), fetchInventory(), fetchOrders()]);
});

function startEdit(order) {
  selectedOrder.value = order;
  editOpen.value = true;
}

function startDelete(order) {
  selectedOrder.value = order;
  deleteOpen.value = true;
}

async function handleAdd(payload) {
  try {
    await addOrder(payload);
    addOpen.value = false;
    success("Order created.");
  } catch (e) {
    error(e.message || "Could not create order");
  }
}

async function handleEdit(payload) {
  if (!selectedOrder.value) return;
  try {
    await updateOrder(selectedOrder.value.id, payload);
    editOpen.value = false;
    success("Order updated.");
  } catch (e) {
    error(e.message || "Could not update order");
  }
}

async function confirmDelete() {
  if (!selectedOrder.value) return;
  try {
    await deleteOrder(selectedOrder.value.id);
    deleteOpen.value = false;
    success("Order deleted.");
  } catch (e) {
    error(e.message || "Could not delete order");
  }
}

async function exportRevenuePdf() {
  try {
    await refreshDashboard();
    exportRevenueReportPdf(dashboard.value);
    success("Revenue report downloaded.");
  } catch (e) {
    error(e.message || "Export failed");
  }
}

function exportOrdersPdfLocal() {
  try {
    exportOrdersPdf(orders.value, customers.value);
    success("Orders PDF downloaded.");
  } catch (e) {
    error(e.message || "Export failed");
  }
}

function exportOrdersXlsxLocal() {
  try {
    exportOrdersXlsx(orders.value);
    success("Orders spreadsheet downloaded.");
  } catch (e) {
    error(e.message || "Export failed");
  }
}
</script>

<template>
  <DashboardLayout title="Orders">
    <div class="mb-5 flex flex-wrap justify-end gap-2">
      <Button v-if="analyticsFull" variant="secondary" @click="exportRevenuePdf">Revenue report PDF</Button>
      <Button v-if="canBulkExport" variant="secondary" @click="exportOrdersPdfLocal">Orders PDF</Button>
      <Button v-if="canBulkExport" variant="secondary" @click="exportOrdersXlsxLocal">Orders Excel</Button>
      <Button @click="addOpen = true">Add Order</Button>
    </div>

    <Spinner v-if="loading" />
    <OrderList v-else :orders="orders" :customers="customers" @edit="startEdit" @delete="startDelete" />

    <AddOrderModal :open="addOpen" :customers="customers" :products="products" @close="addOpen = false" @submit="handleAdd" />
    <EditOrderModal
      :open="editOpen"
      :order="selectedOrder"
      :customers="customers"
      :products="products"
      @close="editOpen = false"
      @submit="handleEdit"
    />
    <Modal :open="deleteOpen" title="Delete Order" @close="deleteOpen = false">
      <p class="text-sm text-slate-500">This action cannot be undone.</p>
      <div class="mt-4 flex justify-end gap-2">
        <Button variant="secondary" @click="deleteOpen = false">Cancel</Button>
        <Button variant="danger" @click="confirmDelete">Delete</Button>
      </div>
    </Modal>
  </DashboardLayout>
</template>
