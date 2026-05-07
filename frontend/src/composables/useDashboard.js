import { ref } from "vue";

import { api } from "../services/api";

const dashboard = ref({
  total_customers: 0,
  total_orders: 0,
  total_revenue: 0,
  gross_sales: 0,
  outstanding_balance: 0,
  monthly_revenue: 0,
  orders_pending: 0,
  orders_partial: 0,
  orders_paid: 0,
  revenue_by_month: [],
  customer_growth: [],
  recent_orders: [],
  upcoming_deliveries: [],
  todays_deliveries: [],
  overdue_deliveries: [],
  pickups_ready: [],
  completed_deliveries: [],
  unread_notifications: 0,
  total_inventory_value: 0,
  low_stock_items: 0,
  out_of_stock_items: 0,
  analytics_limited: false
});

const loading = ref(false);

export async function refreshDashboard() {
  loading.value = true;
  try {
    dashboard.value = await api.getDashboard();
  } finally {
    loading.value = false;
  }
}

export function useDashboard() {
  return { dashboard, loading, refreshDashboard };
}
