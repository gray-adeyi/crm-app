<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import Alert from "../components/ui/Alert.vue";
import Button from "../components/ui/Button.vue";
import Input from "../components/ui/Input.vue";
import { useAuth } from "../composables/useAuth";

const route = useRoute();
const router = useRouter();
const { verifyEmail, resendVerification, loading } = useAuth();

const email = ref("");
const otp = ref("");
const error = ref("");
const info = ref("");
const resendSec = ref(0);

const cooldownLabel = computed(() => (resendSec.value > 0 ? `Resend in ${resendSec.value}s` : "Resend code"));

onMounted(() => {
  const q = route.query.email;
  if (q) email.value = String(q);
});

function startCooldown(seconds) {
  resendSec.value = seconds;
  const t = setInterval(() => {
    resendSec.value -= 1;
    if (resendSec.value <= 0) clearInterval(t);
  }, 1000);
}

async function submit() {
  error.value = "";
  info.value = "";
  const code = String(otp.value).replace(/\D/g, "").slice(0, 8);
  if (code.length < 6) {
    error.value = "Enter the 6-digit code from your email.";
    return;
  }
  try {
    await verifyEmail(email.value.trim(), code);
    router.replace({ name: "dashboard" });
  } catch (err) {
    const d = err.detail;
    if (d && typeof d === "object") {
      error.value = d.message || err.message;
    } else {
      error.value = err.message;
    }
  }
}

async function resend() {
  if (resendSec.value > 0 || loading.value) return;
  error.value = "";
  info.value = "";
  try {
    await resendVerification(email.value.trim());
    info.value = "A new verification code is on its way.";
    startCooldown(60);
  } catch (err) {
    const d = err.detail;
    if (d && typeof d === "object" && d.code === "OTP_COOLDOWN") {
      startCooldown(Number(d.retry_after_sec) || 45);
      info.value = "Please wait before requesting another code.";
    } else {
      error.value = err.message;
    }
  }
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden p-4">
    <div
      aria-hidden="true"
      class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.16),_transparent_50%),radial-gradient(ellipse_at_bottom,_rgba(14,165,233,0.12),_transparent_45%)]"
    />
    <div
      class="relative z-10 w-full max-w-md rounded-3xl border border-slate-200/80 bg-white/90 p-8 shadow-2xl shadow-slate-900/10 backdrop-blur-md dark:border-slate-700/80 dark:bg-slate-900/90 dark:shadow-black/40"
    >
      <p class="text-xs font-semibold uppercase tracking-widest text-brand-600 dark:text-brand-400">Vendora security</p>
      <h1 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">Verify your email</h1>
      <p class="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Enter the one-time code we sent to finish activating your workspace.
      </p>

      <div class="mt-6 space-y-4">
        <Alert type="error" :message="error" />
        <Alert type="success" :message="info" />

        <Input v-model="email" label="Email" type="email" placeholder="you@company.com" />
        <Input v-model="otp" label="Verification code" maxlength="8" placeholder="6-digit code" autocomplete="one-time-code" />

        <Button :disabled="loading" type="button" block @click="submit">{{ loading ? "Verifying…" : "Verify & continue" }}</Button>
        <button
          type="button"
          class="w-full text-center text-sm font-medium text-brand-600 disabled:opacity-40 dark:text-brand-400"
          :disabled="resendSec > 0 || loading"
          @click="resend"
        >
          {{ cooldownLabel }}
        </button>
        <RouterLink to="/login" class="block text-center text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
          Back to sign in
        </RouterLink>
      </div>
    </div>
  </div>
</template>
