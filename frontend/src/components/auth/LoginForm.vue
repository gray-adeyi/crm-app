<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";
import Alert from "../ui/Alert.vue";
import { useAuth } from "../../composables/useAuth";

const email = ref("");
const password = ref("");
const showPassword = ref(false);
const error = ref("");
const { login, loading } = useAuth();
const router = useRouter();

async function submit() {
  error.value = "";
  try {
    await login(email.value, password.value);
    router.push("/");
  } catch (err) {
    const detail = err.detail;
    if (detail && typeof detail === "object" && detail.code === "EMAIL_NOT_VERIFIED") {
      router.push({
        name: "verify-email",
        query: { email: detail.email || email.value }
      });
      return;
    }
    error.value = err.message;
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <Alert type="error" :message="error" />
    <Input v-model="email" label="Email" type="email" placeholder="you@company.com" />
    <Input
      v-model="password"
      label="Password"
      :type="showPassword ? 'text' : 'password'"
      placeholder="Enter your password"
    />
    <button type="button" class="text-xs text-slate-500 hover:text-slate-800" @click="showPassword = !showPassword">
      {{ showPassword ? "Hide" : "Show" }} password
    </button>
    <Button :disabled="loading" type="submit" block>{{ loading ? "Signing in..." : "Sign in" }}</Button>
  </form>
</template>
