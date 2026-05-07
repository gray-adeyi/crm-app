import { computed, ref } from "vue";

import { api } from "../services/api";
import { refreshDashboard } from "./useDashboard";

const items = ref([]);
const loading = ref(false);
const query = ref({ search: "", category: "" });

export function useInventory() {
  const lowStockCount = computed(() => items.value.filter((p) => p.reorder_threshold > 0 && p.quantity_in_stock <= p.reorder_threshold).length);
  const outOfStockCount = computed(() => items.value.filter((p) => Number(p.quantity_in_stock || 0) <= 0).length);

  async function fetchInventory(params = {}) {
    loading.value = true;
    try {
      items.value = await api.getInventory({ ...query.value, ...params });
    } finally {
      loading.value = false;
    }
  }

  async function addItem(payload) {
    await api.addInventoryItem(payload);
    await fetchInventory();
    await refreshDashboard();
  }

  async function updateItem(id, payload) {
    await api.updateInventoryItem(id, payload);
    await fetchInventory();
    await refreshDashboard();
  }

  async function deleteItem(id) {
    await api.deleteInventoryItem(id);
    await fetchInventory();
    await refreshDashboard();
  }

  async function restockItem(id, payload) {
    await api.restockInventoryItem(id, payload);
    await fetchInventory();
    await refreshDashboard();
  }

  return {
    items,
    loading,
    query,
    lowStockCount,
    outOfStockCount,
    fetchInventory,
    addItem,
    updateItem,
    deleteItem,
    restockItem
  };
}

