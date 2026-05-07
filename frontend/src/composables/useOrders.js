import { computed, ref } from "vue";
import { api } from "../services/api";
import { refreshDashboard } from "./useDashboard";

const orders = ref([]);
const loading = ref(false);

export function useOrders() {
  const totalRevenue = computed(() =>
    orders.value.reduce((sum, order) => sum + Number(order.total_price ?? order.price ?? 0), 0)
  );

  async function fetchOrders() {
    loading.value = true;
    try {
      orders.value = await api.getOrders();
    } finally {
      loading.value = false;
    }
  }

  async function addOrder(payload) {
    await api.addOrder(payload);
    await fetchOrders();
    await refreshDashboard();
  }

  async function updateOrder(id, payload) {
    await api.updateOrder(id, payload);
    await fetchOrders();
    await refreshDashboard();
  }

  async function deleteOrder(id) {
    await api.deleteOrder(id);
    await fetchOrders();
    await refreshDashboard();
  }

  return { orders, loading, totalRevenue, fetchOrders, addOrder, updateOrder, deleteOrder };
}
