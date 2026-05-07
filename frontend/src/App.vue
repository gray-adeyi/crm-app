<script setup>
import { onMounted } from "vue";
import { getActivePinia } from "pinia";

import ToastHost from "./components/ui/ToastHost.vue";
import { isAuthenticated } from "./services/auth";
import { useSessionStore } from "./stores/session";

onMounted(async () => {
  const pinia = getActivePinia();
  if (!pinia || !isAuthenticated()) return;
  const session = useSessionStore(pinia);
  if (!session.initialized) {
    await session.loadUser();
  }
});
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
    <RouterView />
    <ToastHost />
  </div>
</template>
