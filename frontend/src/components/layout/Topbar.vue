<script setup>
import { useTheme } from "../../composables/useTheme";

defineProps({
  showMenu: { type: Boolean, default: true },
  title: { type: String, default: "" },
  subtitle: { type: String, default: "" }
});

defineEmits(["menu"]);
const { isDark, toggleTheme } = useTheme();
</script>

<template>
  <header class="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
    <div class="flex items-center gap-3">
      <button
        v-if="showMenu"
        class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden dark:text-slate-200 dark:hover:bg-slate-800"
        @click="$emit('menu')"
      >
        ☰
      </button>
      <div class="min-w-0">
      <h1 class="truncate text-xl font-semibold tracking-tight text-slate-900 dark:text-white">{{ title }}</h1>
      <p v-if="subtitle" class="line-clamp-2 text-sm text-slate-600 dark:text-slate-300">{{ subtitle }}</p>
      <p v-else class="text-sm text-slate-500 dark:text-slate-400">Operate your commerce CRM with institutional polish.</p>
      </div>
    </div>
    <button
      class="rounded-lg px-3 py-1.5 text-xs font-medium ring-1 ring-slate-300 hover:bg-slate-100 dark:ring-slate-700 dark:hover:bg-slate-800"
      @click="toggleTheme"
    >
      {{ isDark ? "Light" : "Dark" }} mode
    </button>
  </header>
</template>
