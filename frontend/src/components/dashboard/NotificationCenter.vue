<script setup>
import { onMounted, ref } from "vue";

import Button from "../ui/Button.vue";
import Spinner from "../ui/Spinner.vue";
import { api } from "../../services/api";
import { useToast } from "../../composables/useToast";
import { refreshDashboard } from "../../composables/useDashboard";

const { error, success } = useToast();
const loading = ref(false);
const items = ref([]);

function badgeClass(n) {
  if (n.severity === "critical") return "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-900/20 dark:text-rose-200 dark:ring-rose-900/40";
  if (n.severity === "warning") return "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-900/20 dark:text-amber-200 dark:ring-amber-900/40";
  return "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700";
}

async function fetchNotifications() {
  loading.value = true;
  try {
    items.value = await api.getNotifications();
  } catch (e) {
    error(e.message || "Could not load notifications");
  } finally {
    loading.value = false;
  }
}

async function markAllRead() {
  const unread = items.value.filter((n) => !n.is_read).map((n) => n.id);
  if (!unread.length) return;
  try {
    await api.markNotificationsRead(unread);
    success("Marked as read.");
    await Promise.all([fetchNotifications(), refreshDashboard()]);
  } catch (e) {
    error(e.message || "Could not mark read");
  }
}

onMounted(fetchNotifications);
</script>

<template>
  <div class="rounded-2xl bg-white p-5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-lg font-semibold">Notifications</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400">Reminders and low-stock alerts.</p>
      </div>
      <div class="flex gap-2">
        <Button variant="secondary" size="sm" @click="fetchNotifications">Refresh</Button>
        <Button size="sm" @click="markAllRead">Mark all read</Button>
      </div>
    </div>

    <Spinner v-if="loading" />
    <ul v-else class="mt-4 space-y-3">
      <li v-for="n in items" :key="n.id" class="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold" :class="n.is_read ? 'text-slate-600 dark:text-slate-300' : 'text-slate-900 dark:text-white'">
              {{ n.title }}
            </p>
            <p v-if="n.body" class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{{ n.body }}</p>
          </div>
          <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1" :class="badgeClass(n)">
            {{ n.type }}
          </span>
        </div>
      </li>
      <li v-if="!items.length" class="text-sm text-slate-500 dark:text-slate-400">No notifications yet.</li>
    </ul>
  </div>
</template>

