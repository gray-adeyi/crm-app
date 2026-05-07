<script setup>
import { computed, onMounted, ref } from "vue";

import AddCustomerModal from "../components/customers/AddCustomerModal.vue";
import CustomerList from "../components/customers/CustomerList.vue";
import EditCustomerModal from "../components/customers/EditCustomerModal.vue";
import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import Modal from "../components/ui/Modal.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useToast } from "../composables/useToast";
import { useCustomers } from "../composables/useCustomers";
import { exportCustomersPdf, exportCustomersXlsx } from "../utils/documents";
import { useSessionStore } from "../stores/session";

const { success, error } = useToast();
const { search, loading, filteredCustomers, fetchCustomers, addCustomer, updateCustomer, deleteCustomer } =
  useCustomers();
const addOpen = ref(false);
const editOpen = ref(false);
const deleteOpen = ref(false);
const selectedCustomer = ref(null);
const session = useSessionStore();
const canBulkExport = computed(() => !!session.user?.can_bulk_export);

onMounted(fetchCustomers);

function startEdit(customer) {
  selectedCustomer.value = customer;
  editOpen.value = true;
}

function startDelete(customer) {
  selectedCustomer.value = customer;
  deleteOpen.value = true;
}

async function handleAdd(payload) {
  try {
    await addCustomer(payload);
    addOpen.value = false;
    success("Customer added.");
  } catch (e) {
    error(e.message || "Could not add customer");
  }
}

async function handleEdit(payload) {
  if (!selectedCustomer.value) return;
  try {
    await updateCustomer(selectedCustomer.value.id, payload);
    editOpen.value = false;
    success("Customer updated.");
  } catch (e) {
    error(e.message || "Could not update customer");
  }
}

async function confirmDelete() {
  if (!selectedCustomer.value) return;
  try {
    await deleteCustomer(selectedCustomer.value.id);
    deleteOpen.value = false;
    success("Customer removed.");
  } catch (e) {
    error(e.message || "Could not delete customer");
  }
}

function exportPdf() {
  try {
    exportCustomersPdf(filteredCustomers.value, "Customers");
    success("PDF downloaded.");
  } catch (e) {
    error(e.message || "Export failed");
  }
}

function exportXlsx() {
  try {
    exportCustomersXlsx(filteredCustomers.value);
    success("Spreadsheet downloaded.");
  } catch (e) {
    error(e.message || "Export failed");
  }
}
</script>

<template>
  <DashboardLayout title="Customers">
    <div class="mb-5 flex flex-wrap items-center gap-3">
      <div class="min-w-[240px] flex-1">
        <Input v-model="search" placeholder="Search customers..." />
      </div>
      <Button v-if="canBulkExport" variant="secondary" @click="exportPdf">Export PDF</Button>
      <Button v-if="canBulkExport" variant="secondary" @click="exportXlsx">Export Excel</Button>
      <Button @click="addOpen = true">Add Customer</Button>
    </div>

    <Spinner v-if="loading" />
    <CustomerList v-else :customers="filteredCustomers" @edit="startEdit" @delete="startDelete" />

    <AddCustomerModal :open="addOpen" @close="addOpen = false" @submit="handleAdd" />
    <EditCustomerModal :open="editOpen" :customer="selectedCustomer" @close="editOpen = false" @submit="handleEdit" />
    <Modal :open="deleteOpen" title="Delete Customer" @close="deleteOpen = false">
      <p class="text-sm text-slate-500">Are you sure you want to remove this customer?</p>
      <div class="mt-4 flex justify-end gap-2">
        <Button variant="secondary" @click="deleteOpen = false">Cancel</Button>
        <Button variant="danger" @click="confirmDelete">Delete</Button>
      </div>
    </Modal>
  </DashboardLayout>
</template>
