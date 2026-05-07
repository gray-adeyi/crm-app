import { defineStore } from "pinia";

import { api } from "../services/api";
import { clearToken, getToken } from "../services/auth";

export const useSessionStore = defineStore("session", {
  state: () => ({
    user: null,
    initialized: false
  }),
  actions: {
    async loadUser() {
      if (!getToken()) {
        this.user = null;
        this.initialized = true;
        return null;
      }
      try {
        this.user = await api.getMe();
        return this.user;
      } catch (err) {
        const status = err?.status ?? err?.response?.status;
        if (status === 401) {
          clearToken();
        }
        this.user = null;
        return null;
      } finally {
        this.initialized = true;
      }
    },
    clearUser() {
      this.user = null;
      this.initialized = true;
    },
    patchLocalUser(patch) {
      if (this.user) Object.assign(this.user, patch);
    }
  }
});
