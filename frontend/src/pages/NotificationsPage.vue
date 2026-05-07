<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";

import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useNotificationsRealtime } from "../composables/useNotificationsRealtime.js";
import { useToast } from "../composables/useToast";
import { api } from "../services/api";

const { success, error: toastErr } = useToast();

const loading = ref(true);
const rows = ref([]);
const counts = ref({ total: 0, unread: 0 });

const filters = ref("all");

async function load() {
  loading.value = true;
  try {
    const [list, cnt] = await Promise.all([
      api.getNotifications({ limit: "400" }),
      api.getNotificationCounts().catch(() => ({
        unread: rows.value.filter((x) => !x.is_read).length,
        total: rows.value.length
      }))
    ]);
    rows.value = Array.isArray(list) ? list : [];
    counts.value = cnt && typeof cnt === "object" ? cnt : { total: rows.value.length, unread: rows.value.filter((r) => !r.is_read).length };
  } catch (e) {
    toastErr(e.message || "Could not load notifications");
  } finally {
    loading.value = false;
  }
}

const visible = computed(() => {
  let src = rows.value;
  if (filters.value === "unread") src = src.filter((n) => !n.is_read);
  return src.filter((n) => catMatch(n));
});

function catMatch(n) {
  const cat = (n.category || "").toLowerCase();
  const t = (n.type || "").toLowerCase();
  const f = filters.value;
  if (f === "all" || f === "unread") return true;
  if (f === "orders") return cat === "orders" || cat === "deliveries" || t.includes("order");
  if (f === "deliveries") return cat === "deliveries";
  if (f === "payments") return cat === "payments" || t.includes("payment");
  if (f === "inventory") return cat === "inventory";
  if (f === "billing") return cat === "billing";
  return true;
}

async function markRead(ids) {
  try {
    await api.markNotificationsRead(ids);
    success("Marked as read");
    await load();
  } catch (e) {
    toastErr(e.message);
  }
}

async function markAllRead() {
  try {
    await api.markAllNotificationsRead();
    success("All caught up.");
    await load();
  } catch (e) {
    toastErr(e.message);
  }
}

async function removeOne(id) {
  try {
    await api.deleteNotification(id);
    await load();
  } catch (e) {
    toastErr(e.message);
  }
}

const tabs = computed(() => [
  { slug: "all", label: "All", badge: counts.value.total },
  { slug: "unread", label: "Unread", badge: counts.value.unread },
  { slug: "orders", label: "Orders" },
  { slug: "deliveries", label: "Deliveries" },
  { slug: "payments", label: "Payments" },
  { slug: "inventory", label: "Inventory" },
  { slug: "billing", label: "Billing" }
]);

function iconFor(n) {
  const c = (n.category || "").toLowerCase();
  if (c === "inventory") return "📦";
  if (c === "deliveries") return "🚚";
  if (c === "billing" || c === "payments") return "💳";
  if (c === "customers") return "👤";
  return "🔔";
}

function formatTs(iso) {
  if (!iso) return "";
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
  } catch {
    return iso;
  }
}

const rt = useNotificationsRealtime(() => load().catch(() => {}));
let poll;

onMounted(() => {
  load();
  rt.subscribe();
  poll = window.setInterval(() => load(), 90000);
});

onUnmounted(() => {
  if (poll) window.clearInterval(poll);
  rt.dispose();
});
</script>

<template>
  <DashboardLayout
    title="Notifications"
    heading-note="Operational signals across orders, payouts, inventory, delivery, billing, and mirrored email alerts."
  >

    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.slug"
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition hover:shadow-soft"
          :class="
            filters === tab.slug
              ? 'border-brand-500 bg-brand-50 text-brand-800 ring-2 ring-brand-200 dark:border-brand-400 dark:bg-brand-950/50 dark:text-brand-100 dark:ring-brand-900'
              : 'border-slate-200 bg-white text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200'
          "
          @click="filters = tab.slug"
        >
          {{ tab.label }}
          <span
            v-if="tab.badge != null && tab.slug === 'unread' && tab.badge > 0"
            class="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-semibold text-white dark:bg-white dark:text-slate-900"
            >{{ tab.badge }}</span
          >
        </button>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="secondary" @click="markAllRead">Mark all read</Button>
        <Button variant="ghost" class="hidden px-3 py-2 sm:inline" @click="load">Refresh</Button>
      </div>
    </div>

    <Spinner v-if="loading" />

    <div v-else-if="visible.length === 0" class="rounded-3xl border border-dashed border-slate-300 bg-white/60 px-10 py-20 text-center dark:border-slate-700 dark:bg-slate-900/40">
      <p class="text-lg font-medium text-slate-800 dark:text-slate-100">You are fully caught up.</p>
      <p class="mt-2 max-w-md mx-auto text-sm text-slate-500 dark:text-slate-400">
        Alerts for deliveries, payouts, subscriptions, inventory, and system events will appear here. We keep this channel realtime-ready — connect WebSockets later without
        changing this UI.
      </p>
    </div>

    <transition-group v-else name="fade-pop" tag="ul" class="space-y-3">
      <li
        v-for="n in visible"
        :key="n.id"
        class="group relative rounded-2xl border border-slate-200 bg-white p-4 shadow-soft transition hover:-translate-y-0.5 hover:shadow-xl dark:border-slate-700 dark:bg-slate-900 dark:shadow-none"
      >
        <div
          class="pointer-events-none absolute inset-x-4 top-4 h-1 rounded-full opacity-70"
          :class="!n.is_read ? 'bg-gradient-to-r from-brand-400 to-brand-600' : 'bg-transparent'"
        />
        <div class="mt-4 flex gap-4">
          <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl dark:bg-slate-800">{{ iconFor(n) }}</span>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ n.category }}</p>
                <h2 class="text-base font-semibold text-slate-900 dark:text-white">{{ n.title }}</h2>
              </div>
              <span class="text-xs text-slate-400 dark:text-slate-500">{{ formatTs(n.created_at) }}</span>
            </div>
            <p v-if="n.body" class="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{{ n.body }}</p>
            <div class="mt-4 flex flex-wrap gap-2">
              <RouterLink v-if="n.action_route" :to="n.action_route" class="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-brand-500">
                {{ n.action_label || "Open" }}
              </RouterLink>
              <button
                type="button"
                class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                :disabled="n.is_read"
                @click="markRead([n.id])"
              >
                {{ n.is_read ? "Read" : "Mark read" }}
              </button>
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                @click="removeOne(n.id)"
              >
                Archive
              </button>
              <span
                class="rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ring-1"
                :class="
                  (n.severity || 'info') === 'critical'
                    ? 'bg-rose-50 text-rose-800 ring-rose-100 dark:bg-rose-950/50 dark:text-rose-100'
                    : n.severity === 'warning'
                      ? 'bg-amber-50 text-amber-900 ring-amber-100 dark:bg-amber-950/40 dark:text-amber-100'
                      : 'bg-slate-50 text-slate-700 ring-slate-100 dark:bg-slate-800 dark:text-slate-300'
                "
                >{{ n.severity }}</span
              >
            </div>
            <div
              v-if="n.notification_channel_email"
              class="mt-2 inline-flex rounded-lg bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-100"
            >
              Email mirrored to your vendor inbox
            </div>
          </div>
        </div>
      </li>
    </transition-group>
  </DashboardLayout>
</template>

<style scoped>
.fade-pop-enter-active,
.fade-pop-leave-active {
  transition: all 0.22s ease;
}
.fade-pop-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.fade-pop-leave-to {
  opacity: 0;
}
</style>
