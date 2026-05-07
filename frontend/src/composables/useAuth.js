import { computed, ref } from "vue";
import { getActivePinia } from "pinia";

import { api } from "../services/api";
import { accessTokenRef, clearToken, setToken } from "../services/auth";
import { useSessionStore } from "../stores/session";

const loading = ref(false);

function getSession() {
  const pinia = getActivePinia();
  return pinia ? useSessionStore(pinia) : null;
}

export function useAuth() {
  const token = accessTokenRef;
  const isAuthenticated = computed(() => Boolean(accessTokenRef.value));

  async function login(email, password) {
    loading.value = true;
    try {
      const data = await api.login({ email, password });
      setToken(data.access_token);
      await getSession()?.loadUser();
      return data;
    } finally {
      loading.value = false;
    }
  }

  async function signup(payload) {
    loading.value = true;
    try {
      return await api.signup(payload);
    } finally {
      loading.value = false;
    }
  }

  async function verifyEmail(email, otp) {
    loading.value = true;
    try {
      const data = await api.verifyEmail({ email, otp });
      setToken(data.access_token);
      await getSession()?.loadUser();
      return data;
    } finally {
      loading.value = false;
    }
  }

  async function resendVerification(email) {
    loading.value = true;
    try {
      return await api.resendVerification({ email });
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    clearToken();
    getSession()?.clearUser();
  }

  return { token, loading, isAuthenticated, login, signup, verifyEmail, resendVerification, logout };
}
