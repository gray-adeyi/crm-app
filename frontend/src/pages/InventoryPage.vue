<script setup>
import { onMounted, ref } from "vue";

import AddProductModal from "../components/inventory/AddProductModal.vue";
import EditProductModal from "../components/inventory/EditProductModal.vue";
import InventoryTable from "../components/inventory/InventoryTable.vue";
import RestockModal from "../components/inventory/RestockModal.vue";
import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import Modal from "../components/ui/Modal.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useToast } from "../composables/useToast";
import { useInventory } from "../composables/useInventory";

const { success, error } = useToast();
const { items, loading, query, fetchInventory, addItem, updateItem, deleteItem, restockItem } = useInventory();

const addOpen = ref(false);
const editOpen = ref(false);
const restockOpen = ref(false);
const deleteOpen = ref(false);
const selected = ref(null);

onMounted(async () => {
  await fetchInventory();
});

function startEdit(item) {
  selected.value = item;
  editOpen.value = true;
}
function startRestock(item) {
  selected.value = item;
  restockOpen.value = true;
}
function startDelete(item) {
  selected.value = item;
  deleteOpen.value = true;
}

async function handleAdd(payload) {
  try {
    await addItem(payload);
    addOpen.value = false;
    success("Inventory item added.");
  } catch (e) {
    error(e.message || "Could not add item");
  }
}

async function handleEdit(payload) {
  if (!selected.value) return;
  try {
    await updateItem(selected.value.id, payload);
    editOpen.value = false;
    success("Inventory item updated.");
  } catch (e) {
    error(e.message || "Could not update item");
  }
}

async function handleRestock(payload) {
  if (!selected.value) return;
  try {
    await restockItem(selected.value.id, payload);
    restockOpen.value = false;
    success("Restocked.");
  } catch (e) {
    error(e.message || "Restock failed");
  }
}

async function confirmDelete() {
  if (!selected.value) return;
  try {
    await deleteItem(selected.value.id);
    deleteOpen.value = false;
    success("Deleted.");
  } catch (e) {
    error(e.message || "Delete failed");
  }
}

let searchTimer = null;
function onSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => fetchInventory(), 250);
}
</script>

<template>
  <DashboardLayout title="Inventory">
    <div class="mb-2 flex flex-wrap items-end justify-between gap-3">
      <div class="flex flex-wrap gap-3">
        <Input v-model="query.search" label="Search" placeholder="Name or SKU" @input="onSearch" />
        <Input v-model="query.category" label="Category" placeholder="Bags, Shoes..." @input="onSearch" />
      </div>
      <Button @click="addOpen = true">Add product</Button>
    </div>

    <Spinner v-if="loading" />
    <InventoryTable v-else :items="items" @edit="startEdit" @restock="startRestock" @delete="startDelete" />

    <AddProductModal :open="addOpen" @close="addOpen = false" @submit="handleAdd" />
    <EditProductModal :open="editOpen" :item="selected" @close="editOpen = false" @submit="handleEdit" />
    <RestockModal :open="restockOpen" :item="selected" @close="restockOpen = false" @submit="handleRestock" />

    <Modal :open="deleteOpen" title="Delete inventory item" @close="deleteOpen = false">
      <p class="text-sm text-slate-500">This will remove the product from your inventory list.</p>
      <div class="mt-4 flex justify-end gap-2">
        <Button variant="secondary" @click="deleteOpen = false">Cancel</Button>
        <Button variant="danger" @click="confirmDelete">Delete</Button>
      </div>
    </Modal>
  </DashboardLayout>
</template>

