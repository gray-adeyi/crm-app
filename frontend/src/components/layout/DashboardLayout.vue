<script setup>
import { computed, ref } from "vue";
import Sidebar from "./Sidebar.vue";
import Topbar from "./Topbar.vue";
import { useSessionStore } from "../../stores/session";

const props = defineProps({
  title: { type: String, default: "Dashboard" },
  headingNote: { type: String, default: "" }
});

const mobileOpen = ref(false);
const session = useSessionStore();

const subtitle = computed(() => {
  if (props.headingNote) return props.headingNote;
  const n = session.user?.business_name?.trim();
  if (n) return `Welcome back · ${n}`;
  return session.user?.email ? `Workspace · ${session.user.email}` : "";
});
</script>

<template>
  <div class="flex min-h-screen">
    <div class="hidden md:block">
      <Sidebar />
    </div>
    <main class="flex-1">
      <Topbar :title="props.title" :subtitle="subtitle" @menu="mobileOpen = true" />
      <div class="p-4 md:p-6">
        <slot />
      </div>
    </main>
    <div v-if="mobileOpen" class="fixed inset-0 z-40 md:hidden">
      <div class="absolute inset-0 bg-slate-950/50" @click="mobileOpen = false" />
      <div class="relative h-full">
        <Sidebar mobile @close="mobileOpen = false" />
      </div>
    </div>
  </div>
</template>
