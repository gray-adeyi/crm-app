<script setup>
import LoginForm from "../components/auth/LoginForm.vue";
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-4">
    <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-soft ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <h1 class="mb-1 text-2xl font-semibold">Welcome back to Vendora</h1>
      <p class="mb-6 text-sm text-slate-500 dark:text-slate-400">Sign in to your CRM workspace.</p>
      <LoginForm />
      <p class="mt-6 text-center text-sm text-slate-500">
        New here? <RouterLink class="text-brand-600 hover:underline" to="/signup">Create an account</RouterLink>
      </p>
    </div>
  </div>
</template>
