<script setup>
import { computed, onMounted, ref } from "vue";
import { getActivePinia } from "pinia";
import { useRoute, useRouter } from "vue-router";

import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Modal from "../components/ui/Modal.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useToast } from "../composables/useToast";
import { billingService } from "../services/billing";
import { useSessionStore } from "../stores/session";

const { success, error } = useToast();
const route = useRoute();
const router = useRouter();

const loading = ref(true);
const actionLoading = ref(false);
const plans = ref([]);
const me = ref(null);
const cancelOpen = ref(false);
const cancelReason = ref("");
const transactions = ref([]);

const renewalCountdown = computed(() => {
  if (!me.value?.renewal_date) return null;
  const diff = new Date(me.value.renewal_date).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
});

const statusTone = computed(() => {
  const status = me.value?.status;
  if (status === "active") return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200";
  if (status === "trial") return "bg-sky-100 text-sky-800 dark:bg-sky-950/50 dark:text-sky-200";
  if (status === "trial_expired") return "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-200";
  if (status === "overdue" || status === "failed") return "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200";
  if (status === "cancelled") return "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-200";
  return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200";
});

async function load() {
  loading.value = true;
  try {
    const [p, m, h] = await Promise.all([billingService.getPlans(), billingService.getMe(), billingService.history()]);
    plans.value = p.plans || [];
    me.value = m;
    transactions.value = h.items || [];
  } catch (e) {
    error(e.message || "Could not load billing");
  } finally {
    loading.value = false;
  }
}

async function selectPlan(planId) {
  actionLoading.value = true;
  try {
    const init = await billingService.initializeCheckout(planId);
    if (!init.authorization_url) throw new Error("Could not initialize checkout");
    window.location.href = init.authorization_url;
  } catch (e) {
    error(e.message || "Could not initialize payment");
  } finally {
    actionLoading.value = false;
  }
}

async function verifyPayment(reference) {
  if (!reference) return;
  actionLoading.value = true;
  try {
    me.value = await billingService.verifyCheckout(reference);
    await load();
    const pinia = getActivePinia();
    if (pinia) {
      const session = useSessionStore(pinia);
      await session.loadUser();
    }
    success("Payment verified and subscription activated.");
    router.replace({ name: "billing" });
  } catch (e) {
    error(e.message || "Could not verify payment");
  } finally {
    actionLoading.value = false;
  }
}

async function cancelSubscription() {
  actionLoading.value = true;
  try {
    me.value = await billingService.cancel(cancelReason.value);
    cancelOpen.value = false;
    cancelReason.value = "";
    success("Subscription cancelled.");
    await load();
  } catch (e) {
    error(e.message || "Could not cancel subscription");
  } finally {
    actionLoading.value = false;
  }
}

async function reactivateSubscription() {
  actionLoading.value = true;
  try {
    me.value = await billingService.reactivate();
    success("Subscription reactivated.");
    await load();
  } catch (e) {
    error(e.message || "Could not reactivate subscription");
  } finally {
    actionLoading.value = false;
  }
}

onMounted(async () => {
  const ref = String(route.query.reference || "");
  if (ref) {
    await verifyPayment(ref);
  } else {
    await load();
  }
});
</script>

<template>
  <DashboardLayout title="Billing">
    <Spinner v-if="loading" />
    <div v-else class="space-y-6">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Current plan</p>
            <p class="mt-1 text-2xl font-semibold capitalize">{{ me?.plan_id }}</p>
            <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Billing cycle: {{ me?.billing_cycle || "monthly" }}
              <span v-if="me?.renewal_date"> · Renews {{ new Date(me.renewal_date).toLocaleDateString() }}</span>
            </p>
            <p v-if="renewalCountdown !== null" class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {{ renewalCountdown >= 0 ? `${renewalCountdown} day(s) to renewal` : "Renewal date passed" }}
            </p>
          </div>
          <span class="rounded-full px-3 py-1 text-xs font-medium capitalize" :class="statusTone">
            {{ me?.status }}
          </span>
        </div>
        <div
          v-if="me?.limits?.trial_all_features"
          class="mt-4 rounded-xl border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-100"
        >
          Your active trial unlocks Growth and Enterprise capabilities (customer limits, analytics, and exports) until it ends.
        </div>
        <div v-if="me?.status === 'overdue' || me?.status === 'failed'" class="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          Payment issue detected. Renew to avoid premium feature lock after grace period.
        </div>
        <p v-if="me?.limits?.max_customers" class="mt-2 text-xs text-slate-500">
          Up to {{ me.limits.max_customers }} customers on this tier.
        </p>
        <p v-else class="mt-2 text-xs text-slate-500">Unlimited customers on this tier.</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button v-if="me?.status !== 'cancelled'" variant="secondary" :disabled="actionLoading" @click="cancelOpen = true">Cancel plan</Button>
          <Button v-if="me?.status === 'cancelled' || me?.status === 'overdue' || me?.status === 'failed'" :disabled="actionLoading" @click="reactivateSubscription">
            Reactivate
          </Button>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-3">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-lg font-semibold">{{ plan.name }}</h3>
            <span
              v-if="me?.plan_id === plan.id"
              class="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-800 dark:bg-brand-900/50 dark:text-brand-100"
            >
              Active
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold">₦{{ plan.price_ngn.toLocaleString() }}<span class="text-sm font-normal text-slate-500">/mo</span></p>
          <ul class="mt-4 flex-1 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li v-for="(f, i) in plan.features" :key="i" class="flex gap-2">
              <span class="text-brand-600">✓</span><span>{{ f }}</span>
            </li>
          </ul>
          <Button
            class="mt-6"
            :disabled="me?.plan_id === plan.id || actionLoading"
            :variant="me?.plan_id === plan.id ? 'secondary' : 'primary'"
            @click="selectPlan(plan.id)"
          >
            {{ me?.plan_id === plan.id ? "Current plan" : "Subscribe" }}
          </Button>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h3 class="text-base font-semibold">Transaction history</h3>
        <p class="mb-3 text-xs text-slate-500 dark:text-slate-400">Payments, renewals, and attempts are tracked in real time.</p>
        <div v-if="!transactions.length" class="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700">
          No transactions yet.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[560px] text-left text-sm">
            <thead class="text-xs uppercase text-slate-500">
              <tr>
                <th class="py-2">Reference</th>
                <th class="py-2">Plan</th>
                <th class="py-2">Amount</th>
                <th class="py-2">Status</th>
                <th class="py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in transactions" :key="tx.reference" class="border-t border-slate-100 dark:border-slate-800">
                <td class="py-2 font-mono text-xs">{{ tx.reference }}</td>
                <td class="py-2 capitalize">{{ tx.plan_id }}</td>
                <td class="py-2">₦{{ Number(tx.amount || 0).toLocaleString() }}</td>
                <td class="py-2 capitalize">{{ tx.status }}</td>
                <td class="py-2">{{ new Date(tx.paid_at || tx.created_at).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h3 class="text-base font-semibold">Invoices</h3>
        <p class="mb-3 text-xs text-slate-500 dark:text-slate-400">Auto-generated for successful subscription payments.</p>
        <div v-if="!(me?.invoices || []).length" class="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700">
          No invoices yet.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[560px] text-left text-sm">
            <thead class="text-xs uppercase text-slate-500">
              <tr>
                <th class="py-2">Invoice no</th>
                <th class="py-2">Plan</th>
                <th class="py-2">Amount</th>
                <th class="py-2">Status</th>
                <th class="py-2">Issued</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in me.invoices" :key="inv.invoice_number" class="border-t border-slate-100 dark:border-slate-800">
                <td class="py-2 font-mono text-xs">{{ inv.invoice_number }}</td>
                <td class="py-2 capitalize">{{ inv.plan_id }}</td>
                <td class="py-2">₦{{ Number(inv.amount || 0).toLocaleString() }}</td>
                <td class="py-2 capitalize">{{ inv.status }}</td>
                <td class="py-2">{{ new Date(inv.issued_at).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <Modal :open="cancelOpen" title="Cancel subscription" @close="cancelOpen = false">
      <p class="text-sm text-slate-600 dark:text-slate-300">You will retain access until the current cycle ends.</p>
      <textarea
        v-model="cancelReason"
        rows="3"
        class="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        placeholder="Reason (optional)"
      />
      <div class="mt-4 flex justify-end gap-2">
        <Button variant="secondary" @click="cancelOpen = false">Keep plan</Button>
        <Button variant="danger" :disabled="actionLoading" @click="cancelSubscription">Cancel subscription</Button>
      </div>
    </Modal>
  </DashboardLayout>
</template>
