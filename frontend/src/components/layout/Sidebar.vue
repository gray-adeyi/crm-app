<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "../ui/Button.vue";
import { useAuth } from "../../composables/useAuth";
import { useSessionStore } from "../../stores/session";

defineProps({ mobile: { type: Boolean, default: false } });
const emit = defineEmits(["close"]);
const route = useRoute();
const router = useRouter();
const { logout } = useAuth();
const session = useSessionStore();
const workspace = computed(() => session.user?.business_name?.trim());

const navItems = [
  { name: "Dashboard", path: "/" },
  { name: "Customers", path: "/customers" },
  { name: "Orders", path: "/orders" },
  { name: "Inventory", path: "/inventory" },
  { name: "Analytics", path: "/analytics" },
  { name: "Billing", path: "/billing" },
  { name: "Reports", path: "/reports" },
  { name: "Notifications", path: "/notifications" },
  { name: "Settings", path: "/settings" },
  { name: "Onboarding", path: "/onboarding" }
];

const isActive = computed(() => (path) => route.path === path);

function onLogout() {
  logout();
  emit("close");
  router.push("/login");
}

function onNavigate() {
  emit("close");
}
</script>

<template>
  <aside class="h-full w-64 border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
    <div class="mb-8 px-2">
      <p class="text-lg font-semibold tracking-tight">Vendora</p>
      <p v-if="workspace" class="mt-1 truncate text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ workspace }}</p>
    </div>
    <nav class="space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="block rounded-lg px-3 py-2 text-sm font-medium transition"
        :class="
          isActive(item.path)
            ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-100'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
        "
        @click="onNavigate"
      >
        {{ item.name }}
      </RouterLink>
    </nav>
    <div class="mt-8">
      <Button variant="danger" block @click="onLogout">Logout</Button>
    </div>
  </aside>
</template>
