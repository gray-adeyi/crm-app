<script setup>
import { computed, onMounted } from "vue";

import OrdersStatusBar from "../components/charts/OrdersStatusBar.vue";
import RevenueLineChart from "../components/charts/RevenueLineChart.vue";
import DashboardLayout from "../components/layout/DashboardLayout.vue";
import RevenueCard from "../components/dashboard/RevenueCard.vue";
import StatsCard from "../components/dashboard/StatsCard.vue";
import Spinner from "../components/ui/Spinner.vue";
import { refreshDashboard, useDashboard } from "../composables/useDashboard";

const { dashboard, loading } = useDashboard();

const revenueLabels = computed(() => (dashboard.value.revenue_by_month || []).map((r) => r.month));
const revenueValues = computed(() => (dashboard.value.revenue_by_month || []).map((r) => r.revenue));

const growthLabels = computed(() => (dashboard.value.customer_growth || []).map((r) => r.month));
const growthValues = computed(() => (dashboard.value.customer_growth || []).map((r) => r.new_customers));

onMounted(async () => {
  await refreshDashboard();
});
</script>

<template>
  <DashboardLayout title="Analytics">
    <Spinner v-if="loading" />
    <div v-else class="space-y-6">
      <div
        v-if="dashboard.analytics_limited"
        class="rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50 to-white p-5 text-sm text-sky-950 ring-1 ring-sky-100 dark:border-sky-900 dark:from-sky-950/50 dark:to-slate-950 dark:text-sky-100 dark:ring-sky-900"
      >
        <p class="font-semibold">Analytics scope</p>
        <p class="mt-1 text-sky-900/85 dark:text-sky-100/85">
          Charts reflect a recent window on Starter. Growth and Enterprise unlock the full six-month horizon (included during trial).
        </p>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatsCard label="Monthly revenue" :value="'₦' + Number(dashboard.monthly_revenue || 0).toLocaleString()" />
        <StatsCard label="Pending orders" :value="dashboard.orders_pending" />
        <StatsCard label="Partial payments" :value="dashboard.orders_partial" />
        <StatsCard label="Paid orders" :value="dashboard.orders_paid" />
      </div>
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 lg:col-span-2">
          <h3 class="mb-2 text-lg font-semibold">Revenue trend</h3>
          <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
            {{ dashboard.analytics_limited ? "Collected payments (recent months on Starter)." : "Collected payments by month (last 6 months)." }}
          </p>
          <RevenueLineChart :labels="revenueLabels" :values="revenueValues" />
        </div>
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <h3 class="mb-2 text-lg font-semibold">Order status mix</h3>
          <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">Snapshot across your workspace.</p>
          <OrdersStatusBar
            :pending="dashboard.orders_pending"
            :partial="dashboard.orders_partial"
            :paid="dashboard.orders_paid"
          />
        </div>
      </div>
      <div class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <h3 class="mb-2 text-lg font-semibold">Customer acquisition</h3>
          <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">New customers per month.</p>
          <RevenueLineChart :labels="growthLabels" :values="growthValues" label="New customers" :currency-format="false" />
        </div>
        <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <h3 class="mb-2 text-lg font-semibold">Lifetime performance</h3>
          <div class="grid gap-4 sm:grid-cols-2">
            <RevenueCard :amount="dashboard.total_revenue" />
            <StatsCard label="Outstanding" :value="dashboard.outstanding_balance" />
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
