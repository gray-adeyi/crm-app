<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";

import RevenueLineChart from "../components/charts/RevenueLineChart.vue";
import SalesBarChart from "../components/charts/SalesBarChart.vue";
import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useSessionStore } from "../stores/session";
import { useToast } from "../composables/useToast";
import { api } from "../services/api";
import { exportReportSummaryPdf, exportReportSummaryXlsx } from "../utils/reportExports.js";

const session = useSessionStore();
const { error } = useToast();

const loading = ref(true);
const summary = ref(null);
const dispatches = ref([]);
const customers = ref([]);

const filters = reactive({
  dateFrom: "",
  dateTo: "",
  orderStatus: "", // csv single for simplicity
  paymentStatus: "",
  customerId: ""
});

const presets = [
  { label: "Last 30 days", from: () => offsetDate(-30), to: () => todayIso() },
  { label: "This month", from: () => startOfMonth(), to: () => todayIso() },
  { label: "Quarter", from: () => offsetDate(-90), to: () => todayIso() }
];

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function startOfMonth() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function applyPreset(p) {
  filters.dateFrom = p.from();
  filters.dateTo = p.to();
  load();
}

async function load() {
  loading.value = true;
  try {
    const params = {};
    if (filters.dateFrom) params.date_from = filters.dateFrom;
    if (filters.dateTo) params.date_to = filters.dateTo;
    if (filters.orderStatus) params.order_status = [filters.orderStatus];
    if (filters.paymentStatus) params.payment_status = [filters.paymentStatus];
    if (filters.customerId) params.customer_id = Number(filters.customerId);

    const [s, d, c] = await Promise.all([
      api.getReportSummary(params),
      api.getMonthlyDispatches().catch(() => ({ items: [] })),
      api.getCustomers().catch(() => [])
    ]);
    summary.value = s;
    dispatches.value = d?.items || [];
    customers.value = Array.isArray(c) ? c : [];
  } catch (e) {
    error(e.message || "Unable to load report");
  } finally {
    loading.value = false;
  }
}

function downloadPdf() {
  if (!summary.value) return;
  exportReportSummaryPdf(summary.value, session.user?.business_name);
}

function downloadXlsx() {
  if (!summary.value) return;
  exportReportSummaryXlsx(summary.value);
}

const revenueLabels = computed(() => (summary.value?.revenue_by_day || []).map((x) => x.date));
const revenueVals = computed(() => (summary.value?.revenue_by_day || []).map((x) => x.revenue));

const statusLabels = computed(() => Object.keys(summary.value?.status_breakdown || {}));
const statusVals = computed(() => Object.values(summary.value?.status_breakdown || {}));

const insightCards = computed(() => {
  if (!summary.value) return [];
  const s = summary.value;
  return [
    {
      title: "Best sellers",
      body:
        (s.bestsellers || []).slice(0, 4).map((b) => `${b.product} · ${b.units_sold} u · ₦${Number(b.revenue || 0).toLocaleString()}`) || []
    },
    {
      title: "Top patrons",
      body: (s.top_customers || []).slice(0, 4).map((c) => `${c.name || "Customer"} · ₦${Number(c.revenue || 0).toLocaleString()}`)
    },
    {
      title: "Inventory pressure",
      body: (s.low_stock_items || []).slice(0, 5).map((p) => `${p.name} · ${p.quantity} left`)
    }
  ];
});

onMounted(load);
</script>

<template>
  <DashboardLayout
    title="Reports & Analytics"
    heading-note="Composable revenue intelligence with Chart.js viz, SLA-friendly exports, and scheduled email parity via dispatch history."
  >

    <div class="mb-6 flex flex-col gap-3 rounded-3xl border border-slate-200/80 bg-white/80 p-4 shadow-soft backdrop-blur dark:border-slate-800 dark:bg-slate-900/60 lg:flex-row lg:items-end lg:justify-between">
      <div class="grid flex-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Input v-model="filters.dateFrom" label="From" type="date" />
        <Input v-model="filters.dateTo" label="To" type="date" />
        <div class="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
          <p class="text-xs font-medium text-slate-600 dark:text-slate-400">Quick ranges</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="p in presets"
              :key="p.label"
              type="button"
              class="rounded-full border border-slate-300 px-3 py-1 text-xs dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800"
              @click="applyPreset(p)"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-600 dark:text-slate-400">Order status</label>
          <select
            v-model="filters.orderStatus"
            class="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950"
          >
            <option value="">All</option>
            <option value="pending">pending</option>
            <option value="partial">partial</option>
            <option value="paid">paid</option>
            <option value="delivered">delivered</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-600 dark:text-slate-400">Payment</label>
          <select
            v-model="filters.paymentStatus"
            class="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950"
          >
            <option value="">All</option>
            <option value="unpaid">unpaid</option>
            <option value="partial">partial paid</option>
            <option value="paid">paid</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-600 dark:text-slate-400">Customer</label>
          <select
            v-model="filters.customerId"
            class="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950"
          >
            <option value="">All customers</option>
            <option v-for="cust in customers" :key="cust.id" :value="String(cust.id)">{{ cust.name }}</option>
          </select>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="secondary" @click="load">Apply</Button>
        <Button variant="secondary" @click="downloadPdf">Export PDF</Button>
        <Button variant="ghost" class="ring-1 ring-slate-300 dark:ring-slate-600" @click="downloadXlsx">Export Excel</Button>
      </div>
    </div>

    <Spinner v-if="loading" />

    <div v-else-if="summary" class="space-y-6">
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 shadow-soft dark:border-slate-700 dark:from-slate-900 dark:to-slate-950">
          <p class="text-xs uppercase tracking-wide text-slate-500">Total revenue</p>
          <p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">₦{{ Number(summary.total_revenue || 0).toLocaleString() }}</p>
          <p class="mt-2 text-xs text-slate-500">Pending balances ₦{{ Number(summary.pending_balance_total || 0).toLocaleString() }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 shadow-soft dark:border-slate-700 dark:from-slate-900 dark:to-slate-950">
          <p class="text-xs uppercase tracking-wide text-slate-500">Slices</p>
          <ul class="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-300">
            <li>Weekly · ₦{{ Number(summary.weekly_revenue || 0).toLocaleString() }}</li>
            <li>Monthly (cal.) · ₦{{ Number(summary.monthly_revenue || 0).toLocaleString() }}</li>
            <li>YTD slice · ₦{{ Number(summary.yearly_revenue || 0).toLocaleString() }}</li>
          </ul>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-emerald-50/70 p-5 shadow-soft dark:border-slate-700 dark:from-slate-900 dark:to-emerald-950/30">
          <p class="text-xs uppercase tracking-wide text-slate-500">Paid vs partial</p>
          <p class="mt-2 text-xl font-semibold text-emerald-700 dark:text-emerald-300">Paid ₦{{ Number(summary.paid_revenue || 0).toLocaleString() }}</p>
          <p class="mt-2 text-lg text-emerald-600 dark:text-emerald-400">Partial ₦{{ Number(summary.partial_revenue || 0).toLocaleString() }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-violet-50/80 p-5 shadow-soft dark:border-slate-700 dark:from-slate-900 dark:to-violet-950/40">
          <p class="text-xs uppercase tracking-wide text-slate-500">Throughput</p>
          <p class="mt-3 text-xl font-semibold text-slate-900 dark:text-white">{{ summary.order_count }} orders · AOV ₦{{ Number(summary.average_order_value || 0).toLocaleString() }}</p>
          <p v-if="summary.delivery_success_rate != null" class="mt-2 text-sm text-slate-600 dark:text-slate-300">{{ summary.delivery_success_rate }}% delivery success (est.)</p>
          <p v-else class="mt-2 text-sm text-slate-500 dark:text-slate-400">Add delivery orders to populate fulfillment SLAs.</p>
        </div>
      </div>

      <div class="grid gap-4 xl:grid-cols-3">
        <div class="xl:col-span-2 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft dark:border-slate-800 dark:bg-slate-900">
          <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Revenue trend</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">Filtered window · collected cash</p>
            </div>
          </div>
          <div class="mt-8 sm:mt-0">
            <RevenueLineChart v-if="revenueLabels.length" :labels="revenueLabels" :values="revenueVals" label="Collected (filtered)" />
            <p v-else class="rounded-2xl border border-dashed border-slate-200 p-16 text-center text-sm text-slate-500 dark:border-slate-700">Chart needs at least two days of data inside the filters.</p>
          </div>
        </div>
        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft dark:border-slate-800 dark:bg-slate-900">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Orders by status</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400">Bar mix for the filtered cohort</p>
          <SalesBarChart v-if="statusLabels.length" class="mt-6" :labels="statusLabels" :values="statusVals" label="Orders" horizontal />
          <p v-else class="mt-16 text-center text-sm text-slate-500 dark:text-slate-400">No orders in selection.</p>
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft dark:border-slate-800 dark:bg-slate-900">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Acquisition</h3>
          <p class="mb-6 text-xs text-slate-500 dark:text-slate-400">New customers captured per month · global context</p>
          <SalesBarChart
            :labels="(summary.customer_growth || []).map((g) => g.month)"
            :values="(summary.customer_growth || []).map((g) => g.new_customers)"
            label="New customers"
            color="#06b6d4"
          />
        </div>
        <div class="grid gap-4 sm:grid-cols-3">
          <div
            v-for="card in insightCards"
            :key="card.title"
            class="rounded-2xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 shadow-soft dark:border-slate-800 dark:from-slate-900 dark:to-slate-950"
          >
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ card.title }}</p>
            <ul class="mt-3 space-y-2 text-xs text-slate-700 dark:text-slate-200">
              <li v-for="(line, idx) in card.body" :key="idx">{{ line }}</li>
              <li v-if="!card.body?.length">No items to display yet.</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft dark:border-slate-800 dark:bg-slate-900">
        <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Scheduled monthly reports</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400">Automated Stripe-style digests mirrored with email dispatch telemetry.</p>
          </div>
          <RouterLink to="/billing" class="rounded-full bg-brand-600 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-brand-500">
            Billing & receipts
          </RouterLink>
        </div>
        <div class="divide-y divide-slate-100 dark:divide-slate-800">
          <div v-for="dispatch in dispatches" :key="dispatch.id + dispatch.period_key" class="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
            <div class="flex flex-wrap gap-2 font-medium capitalize text-slate-800 dark:text-slate-100">
              <span class="rounded-full bg-emerald-50 px-2 py-1 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-50">{{ dispatch.report_kind?.replace('_', ' ') }}</span>
              <span>{{ dispatch.period_key }}</span>
            </div>
            <span class="text-xs text-slate-500">{{ dispatch.sent_at ? new Date(dispatch.sent_at).toLocaleString() : '' }}</span>
          </div>
          <div v-if="dispatches.length === 0" class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            Automated PDFs attach to outbound mail at month start · history populates automatically.
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
