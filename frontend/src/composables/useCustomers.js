import { computed, ref } from "vue";
import { api } from "../services/api";
import { refreshDashboard } from "./useDashboard";

const customers = ref([]);
const loading = ref(false);
const search = ref("");

export function useCustomers() {
  const filteredCustomers = computed(() =>
    customers.value.filter((customer) =>
      customer.name.toLowerCase().includes(search.value.toLowerCase())
    )
  );

  async function fetchCustomers() {
    loading.value = true;
    try {
      customers.value = await api.getCustomers();
    } finally {
      loading.value = false;
    }
  }

  async function addCustomer(payload) {
    await api.addCustomer(payload);
    await fetchCustomers();
    await refreshDashboard();
  }

  async function updateCustomer(id, payload) {
    await api.updateCustomer(id, payload);
    await fetchCustomers();
    await refreshDashboard();
  }

  async function deleteCustomer(id) {
    await api.deleteCustomer(id);
    await fetchCustomers();
    await refreshDashboard();
  }

  return {
    customers,
    loading,
    search,
    filteredCustomers,
    fetchCustomers,
    addCustomer,
    updateCustomer,
    deleteCustomer
  };
}
