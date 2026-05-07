<script setup>
import { onMounted, reactive, ref } from "vue";
import { getActivePinia } from "pinia";

import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import Spinner from "../components/ui/Spinner.vue";
import { useToast } from "../composables/useToast";
import { api } from "../services/api";
import { useSessionStore } from "../stores/session";

const { success, error } = useToast();
const loading = ref(true);
const saving = ref(false);
const form = reactive({ business_name: "", currency: "NGN", logo_url: "" });

async function load() {
  loading.value = true;
  try {
    const pinia = getActivePinia();
    const session = pinia ? useSessionStore(pinia) : null;
    if (session && !session.user) await session.loadUser();
    const u = session?.user;
    if (u) {
      form.business_name = u.business_name || "";
      form.currency = u.currency || "NGN";
      form.logo_url = u.logo_url || "";
    }
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    const updated = await api.patchProfile({
      business_name: form.business_name || null,
      currency: form.currency || "NGN",
      logo_url: form.logo_url || null
    });
    const pinia = getActivePinia();
    if (pinia) {
      useSessionStore(pinia).patchLocalUser(updated);
    }
    success("Settings saved.");
  } catch (e) {
    error(e.message || "Could not save");
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <DashboardLayout title="Settings">
    <Spinner v-if="loading" />
    <div v-else class="mx-auto max-w-xl space-y-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <div>
        <h2 class="text-lg font-semibold">Business profile</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">Used on invoices and customer touchpoints.</p>
      </div>
      <Input v-model="form.business_name" label="Brand / business name" placeholder="e.g. Lola’s Skincare" />
      <Input v-model="form.currency" label="Currency code" placeholder="NGN" />
      <Input v-model="form.logo_url" label="Logo URL (optional)" placeholder="https://…" />
      <div class="flex justify-end gap-2">
        <Button :disabled="saving" @click="save">{{ saving ? "Saving…" : "Save changes" }}</Button>
      </div>
      <RouterLink class="text-sm font-medium text-brand-700 hover:underline dark:text-brand-300" :to="{ name: 'onboarding' }">
        Re-run onboarding checklist →
      </RouterLink>
    </div>
  </DashboardLayout>
</template>
