<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { getActivePinia } from "pinia";

import DashboardLayout from "../components/layout/DashboardLayout.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import { useToast } from "../composables/useToast";
import { api } from "../services/api";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const { success, error } = useToast();
const step = ref(1);
const saving = ref(false);
const form = reactive({ business_name: "", currency: "NGN", logo_url: "" });

function next() {
  step.value = Math.min(3, step.value + 1);
}

function prev() {
  step.value = Math.max(1, step.value - 1);
}

async function finish() {
  saving.value = true;
  try {
    const updated = await api.completeOnboarding({
      business_name: form.business_name,
      currency: form.currency,
      logo_url: form.logo_url || null,
      onboarding_completed: true
    });
    const pinia = getActivePinia();
    if (pinia) {
      useSessionStore(pinia).patchLocalUser(updated);
    }
    success("Welcome aboard — your workspace is ready.");
    router.push({ name: "dashboard" });
  } catch (e) {
    error(e.message || "Could not complete onboarding");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <DashboardLayout title="Onboarding">
    <div class="mx-auto max-w-lg space-y-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <div class="flex items-center gap-2 text-xs font-medium text-slate-500">
        <span :class="step >= 1 ? 'text-brand-600' : ''">1 · Welcome</span>
        <span>→</span>
        <span :class="step >= 2 ? 'text-brand-600' : ''">2 · Business</span>
        <span>→</span>
        <span :class="step >= 3 ? 'text-brand-600' : ''">3 · Finish</span>
      </div>

      <div v-if="step === 1" class="space-y-3">
        <h2 class="text-xl font-semibold">Welcome to Vendora</h2>
        <p class="text-sm text-slate-600 dark:text-slate-300">
          A focused workspace for Nigerian vendors: customers, orders, payments, and analytics in one place.
        </p>
        <div class="flex justify-end">
          <Button @click="next">Continue</Button>
        </div>
      </div>

      <div v-else-if="step === 2" class="space-y-4">
        <h2 class="text-xl font-semibold">Tell us about your business</h2>
        <Input v-model="form.business_name" label="Brand name" placeholder="Your store name" />
        <Input v-model="form.currency" label="Currency" placeholder="NGN" />
        <Input v-model="form.logo_url" label="Logo URL (optional)" />
        <div class="flex justify-between gap-2">
          <Button variant="secondary" @click="prev">Back</Button>
          <Button :disabled="!form.business_name" @click="next">Continue</Button>
        </div>
      </div>

      <div v-else class="space-y-4">
        <h2 class="text-xl font-semibold">You are set</h2>
        <p class="text-sm text-slate-600 dark:text-slate-300">
          Add your first customer and order from the sidebar. You can revisit this wizard anytime from Settings.
        </p>
        <div class="flex justify-between gap-2">
          <Button variant="secondary" @click="prev">Back</Button>
          <Button :disabled="saving || !form.business_name" @click="finish">{{ saving ? "Saving…" : "Finish setup" }}</Button>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
