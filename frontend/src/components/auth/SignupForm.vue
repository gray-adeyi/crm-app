<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import Alert from "../ui/Alert.vue";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import { useAuth } from "../../composables/useAuth";

const companyName = ref("");
const email = ref("");
const password = ref("");
const showPassword = ref(false);
const error = ref("");
const success = ref("");
const { signup, loading } = useAuth();
const router = useRouter();

async function submit() {
  error.value = "";
  success.value = "";
  if (String(companyName.value).trim().length < 2) {
    error.value = "Please enter your company or vendor name.";
    return;
  }
  if (String(password.value).length < 8) {
    error.value = "Password must be at least 8 characters.";
    return;
  }
  try {
    const res = await signup({
      company_name: companyName.value.trim(),
      email: email.value.trim(),
      password: password.value
    });
    success.value = res.message || "Check your inbox for a verification code.";
    setTimeout(() => {
      router.push({ name: "verify-email", query: { email: res.email || email.value } });
    }, 600);
  } catch (err) {
    error.value = err.message;
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <Alert type="error" :message="error" />
    <Alert type="success" :message="success" />
    <Input v-model="companyName" label="Company / vendor name" placeholder="e.g. Sarah Fashion House" />
    <Input v-model="email" label="Email" type="email" placeholder="you@company.com" />
    <Input
      v-model="password"
      label="Password"
      :type="showPassword ? 'text' : 'password'"
      placeholder="At least 8 characters"
    />
    <button type="button" class="text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400" @click="showPassword = !showPassword">
      {{ showPassword ? "Hide" : "Show" }} password
    </button>
    <Button :disabled="loading" type="submit" block>{{ loading ? "Sending code…" : "Create workspace" }}</Button>
  </form>
</template>
