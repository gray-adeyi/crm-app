<script setup>
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";

import AnalyticsChart from "../components/dashboard/AnalyticsChart.vue";
import DeliveryWidgets from "../components/dashboard/DeliveryWidgets.vue";
import NotificationCenter from "../components/dashboard/NotificationCenter.vue";
import RecentOrders from "../components/dashboard/RecentOrders.vue";
import RevenueCard from "../components/dashboard/RevenueCard.vue";
import StatsCard from "../components/dashboard/StatsCard.vue";
import OrdersStatusBar from "../components/charts/OrdersStatusBar.vue";
import RevenueLineChart from "../components/charts/RevenueLineChart.vue";
import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Spinner from "../components/ui/Spinner.vue";
import { refreshDashboard, useDashboard } from "../composables/useDashboard";
import { useSessionStore } from "../stores/session";

const { dashboard, loading } = useDashboard();
const session = useSessionStore();

const trialLabel = computed(() => {
  if (!session.user?.is_trial_active) return null;
  const end = session.user.trial_ends_at || session.user.trial_end_date;
  if (!end) return "Trial active";
  const d = new Date(end);
  const days = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  return days > 0 ? `${days} days left on trial` : "Trial ending today";
});

const planChip = computed(() => (session.user?.current_plan || "starter").replace(/^\w/, (c) => c.toUpperCase()));

const subStatus = computed(() => session.user?.subscription_status || "inactive");

const paidLikeCount = computed(
  () => dashboard.value.recent_orders.filter((o) => ["paid", "delivered"].includes(o.status)).length
);

const pendingLikeCount = computed(
  () => dashboard.value.recent_orders.filter((o) => ["pending", "partial"].includes(o.status)).length
);

const revenueLabels = computed(() => (dashboard.value.revenue_by_month || []).map((r) => r.month));
const revenueValues = computed(() => (dashboard.value.revenue_by_month || []).map((r) => r.revenue));

onMounted(async () => {
  await refreshDashboard();
});
</script>

<template>
  <DashboardLayout title="Dashboard">
    <Spinner v-if="loading" />
    <div v-else class="space-y-6">
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-indigo-600 to-violet-600 p-5 text-white shadow-lg shadow-indigo-500/30 dark:border-indigo-900/50 lg:col-span-2">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-widest text-indigo-100/90">Today</p>
              <h3 class="mt-1 text-xl font-semibold">Operational command</h3>
              <p class="mt-2 max-w-xl text-sm text-indigo-50/90">
                Jump into fulfilment, customer care, or treasury in one click designed for global vendors who run Vendora daily.
              </p>
            </div>
            <div class="rounded-2xl bg-white/12 px-4 py-3 text-right text-sm backdrop-blur">
              <p class="text-[11px] uppercase tracking-wide text-indigo-100/80">Workspace</p>
              <p class="text-base font-semibold">{{ session.user?.business_name || planChip }}</p>
            </div>
          </div>
          <div class="mt-5 flex flex-wrap gap-2">
            <RouterLink
              to="/orders"
              class="inline-flex rounded-xl bg-white px-4 py-2 text-sm font-semibold text-indigo-700 shadow-sm transition hover:bg-indigo-50"
            >
              + New order
            </RouterLink>
            <RouterLink
              to="/customers"
              class="inline-flex rounded-xl border border-white/40 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10"
            >
              Add customer
            </RouterLink>
            <RouterLink
              to="/inventory"
              class="inline-flex rounded-xl border border-white/40 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10"
            >
              Manage stock
            </RouterLink>
            <RouterLink to="/reports" class="inline-flex rounded-xl border border-white/40 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10">
              Insights
            </RouterLink>
          </div>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft ring-1 ring-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:ring-slate-800">
          <p class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Subscription</p>
          <p class="mt-2 text-2xl font-semibold capitalize text-slate-900 dark:text-white">{{ subStatus }}</p>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ planChip }} plan</p>
          <p v-if="trialLabel" class="mt-4 rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-900 dark:bg-sky-950/50 dark:text-sky-100">{{ trialLabel }}</p>
          <RouterLink
            to="/billing"
            class="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-slate-900 py-2 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          >
            Manage billing
          </RouterLink>
        </div>
      </div>
      <div
        v-if="dashboard.analytics_limited"
        class="rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50 to-white p-5 text-sm text-sky-950 ring-1 ring-sky-100 dark:border-sky-900 dark:from-sky-950/50 dark:to-slate-950 dark:text-sky-100 dark:ring-sky-900"
      >
        <p class="font-semibold">Extended analytics overview</p>
        <p class="mt-1 text-sky-900/85 dark:text-sky-100/85">
          You are viewing a curated snapshot on Starter. Upgrade to Growth for full trends, SaaS KPIs like MRR, and churn over six months — free trial includes everything.
        </p>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatsCard label="Total Customers" :value="dashboard.total_customers" />
        <StatsCard label="Total Orders" :value="dashboard.total_orders" />
        <StatsCard label="Outstanding" :value="'₦' + Number(dashboard.outstanding_balance || 0).toLocaleString()" />
        <StatsCard label="Gross Orders" :value="'₦' + Number(dashboard.gross_sales || 0).toLocaleString()" />
        <RevenueCard :amount="dashboard.total_revenue" />
      </div>

      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatsCard label="Inventory value" :value="'₦' + Number(dashboard.total_inventory_value || 0).toLocaleString()" />
        <StatsCard label="Low stock items" :value="dashboard.low_stock_items || 0" />
        <StatsCard label="Out of stock" :value="dashboard.out_of_stock_items || 0" />
        <StatsCard label="Unread notifications" :value="dashboard.unread_notifications || 0" />
      </div>

      <DeliveryWidgets
        :upcoming="dashboard.upcoming_deliveries || []"
        :today="dashboard.todays_deliveries || []"
        :overdue="dashboard.overdue_deliveries || []"
        :pickups="dashboard.pickups_ready || []"
        :completed="dashboard.completed_deliveries || []"
      />

      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatsCard label="This month (collected)" :value="'₦' + Number(dashboard.monthly_revenue || 0).toLocaleString()" />
        <StatsCard label="Pending orders" :value="dashboard.orders_pending" />
        <StatsCard label="Partial payments" :value="dashboard.orders_partial" />
        <StatsCard label="Paid orders" :value="dashboard.orders_paid" />
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <h3 class="mb-1 text-lg font-semibold">Revenue trend</h3>
          <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">Collected payments by month.</p>
          <RevenueLineChart :labels="revenueLabels" :values="revenueValues" />
        </div>
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <h3 class="mb-1 text-lg font-semibold">Order status snapshot</h3>
          <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">Across all orders in your workspace.</p>
          <OrdersStatusBar
            :pending="dashboard.orders_pending"
            :partial="dashboard.orders_partial"
            :paid="dashboard.orders_paid"
          />
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <AnalyticsChart :paid-count="paidLikeCount" :pending-count="pendingLikeCount" />
        <RecentOrders :orders="dashboard.recent_orders" />
      </div>

      <NotificationCenter />
    </div>
  </DashboardLayout>
</template>
