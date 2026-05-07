<script setup>
import SignupForm from "../components/auth/SignupForm.vue";
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden p-4">
    <div
      aria-hidden="true"
      class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.12),transparent_52%),radial-gradient(ellipse_at_bottom,_rgba(14,165,233,0.1),transparent_48%)]"
    />
    <div
      class="relative z-10 w-full max-w-md rounded-[1.65rem] border border-white/70 bg-white/90 p-8 shadow-[0_35px_80px_-34px_rgba(15,23,42,0.45)] ring-1 ring-slate-200/80 backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-950/85 dark:ring-slate-800"
    >
      <p class="text-xs font-semibold uppercase tracking-widest text-brand-600 dark:text-brand-400"> Vendora onboarding</p>
      <h1 class="mb-2 mt-2 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">Launch your storefront CRM</h1>
      <p class="mb-8 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Professional orders, payouts, fulfilment telemetry, analytics, and SaaS subscriptions anchored to a verified inbox.
      </p>
      <SignupForm />
      <p class="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
        Already have an account?
        <RouterLink class="font-medium text-brand-600 hover:text-brand-500 hover:underline dark:text-brand-400" to="/login">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>
