import { ref } from "vue";

const TOKEN_KEY = "token";

/** Mirrors localStorage JWT for Composition API-friendly reactivity. */
export const accessTokenRef = ref(typeof localStorage !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "");

export function getToken() {
  return accessTokenRef.value;
}

export function setToken(token) {
  accessTokenRef.value = token;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  accessTokenRef.value = "";
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return Boolean(accessTokenRef.value);
}
