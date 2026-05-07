import { clearToken, getToken } from "./auth";

/** Set from main.js once the router exists (avoids import cycles). */
let onUnauthorized = null;
let onSubscriptionRequired = null;

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export function setSubscriptionRequiredHandler(handler) {
  onSubscriptionRequired = handler;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function normalizeDetail(payload) {
  const detail = payload?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === "string" ? e : `${e.loc?.join?.(".") || "field"}: ${e.msg}`))
      .join(" · ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return "Something went wrong";
}

async function request(path, options = {}) {
  const token = getToken();

  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
    headers.token = token;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  const data = await response.json().catch(() => ({}));

  if (response.status === 401 && !path.includes("/login") && token) {
    clearToken();
    if (typeof onUnauthorized === "function") {
      try {
        onUnauthorized();
      } catch {
        // ignore router errors — still surface below
      }
    }
    throw new Error(normalizeDetail(data) || "Unauthorized");
  }

  if (response.status === 403 && data?.detail?.code === "SUBSCRIPTION_REQUIRED" && typeof onSubscriptionRequired === "function") {
    if (!path.includes("/billing")) {
      try {
        onSubscriptionRequired();
      } catch {
        // ignore
      }
    }
  }

  if (!response.ok) {
    const msg = normalizeDetail(data) || `Request failed (${response.status})`;
    /** @typedef {{ status?: number; detail?: unknown }} AugmentedApiError */
    const err = /** @type {Error & AugmentedApiError} */ (new Error(msg));
    err.status = response.status;
    err.detail = data?.detail;
    throw err;
  }

  return data;
}

export const api = {
  signup(payload) {
    return request("/signup", { method: "POST", body: JSON.stringify(payload) });
  },

  verifyEmail(payload) {
    return request("/verify-email", { method: "POST", body: JSON.stringify(payload) });
  },

  resendVerification(payload) {
    return request("/resend-verification", { method: "POST", body: JSON.stringify(payload) });
  },

  login(payload) {
    return request("/login", { method: "POST", body: JSON.stringify(payload) });
  },

  getMe() {
    return request("/users/me");
  },

  patchProfile(payload) {
    return request("/users/me", { method: "PATCH", body: JSON.stringify(payload) });
  },

  changePassword(payload) {
    return request("/users/me/password", { method: "POST", body: JSON.stringify(payload) });
  },

  changeEmail(payload) {
    return request("/users/me/email", { method: "POST", body: JSON.stringify(payload) });
  },

  getReportLogs() {
    return request("/reports/logs");
  },

  getReportSummary(params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === null || String(v).length === 0) return;
      if (Array.isArray(v)) v.forEach((x) => qs.append(k, String(x)));
      else qs.append(k, String(v));
    });
    const s = qs.toString();
    return request(`/reports/summary${s ? `?${s}` : ""}`);
  },

  getMonthlyDispatches() {
    return request("/reports/monthly-dispatches");
  },

  completeOnboarding(payload) {
    return request("/users/me/onboarding", { method: "POST", body: JSON.stringify(payload) });
  },

  getDashboard() {
    return request("/dashboard");
  },

  getCustomers() {
    return request("/customers");
  },

  addCustomer(payload) {
    return request("/customers", { method: "POST", body: JSON.stringify(payload) });
  },

  updateCustomer(id, payload) {
    return request(`/customers/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  },

  deleteCustomer(id) {
    return request(`/customers/${id}`, { method: "DELETE" });
  },

  getOrders() {
    return request("/orders");
  },

  addOrder(payload) {
    return request("/orders", { method: "POST", body: JSON.stringify(payload) });
  },

  updateOrder(id, payload) {
    return request(`/orders/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  },

  deleteOrder(id) {
    return request(`/orders/${id}`, { method: "DELETE" });
  },

  getInventory(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && String(v).length > 0)
    ).toString();
    return request(`/inventory${qs ? `?${qs}` : ""}`);
  },

  addInventoryItem(payload) {
    return request("/inventory", { method: "POST", body: JSON.stringify(payload) });
  },

  updateInventoryItem(id, payload) {
    return request(`/inventory/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  },

  deleteInventoryItem(id) {
    return request(`/inventory/${id}`, { method: "DELETE" });
  },

  restockInventoryItem(id, payload) {
    return request(`/inventory/${id}/restock`, { method: "POST", body: JSON.stringify(payload) });
  },

  getInventoryAnalytics() {
    return request("/inventory/analytics");
  },

  getNotifications(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && String(v).length > 0)
    ).toString();
    return request(`/notifications${qs ? `?${qs}` : ""}`);
  },

  getNotificationCounts() {
    return request("/notifications/counts");
  },

  markNotificationsRead(ids) {
    return request("/notifications/mark-read", { method: "POST", body: JSON.stringify({ ids }) });
  },

  markAllNotificationsRead() {
    return request("/notifications/mark-all-read", { method: "POST" });
  },

  deleteNotification(id) {
    return request(`/notifications/${id}`, { method: "DELETE" });
  },

  getBillingPlans() {
    return request("/billing/plans");
  },

  getBillingMe() {
    return request("/billing/me");
  },

  initializeSubscription(planId) {
    return request("/billing/subscribe/initialize", { method: "POST", body: JSON.stringify({ plan_id: planId }) });
  },

  verifySubscription(reference) {
    return request("/billing/subscribe/verify", { method: "POST", body: JSON.stringify({ reference }) });
  },

  cancelSubscription(reason) {
    return request("/billing/cancel", { method: "POST", body: JSON.stringify({ reason: reason || null }) });
  },

  reactivateSubscription() {
    return request("/billing/reactivate", { method: "POST" });
  },

  getBillingTransactions() {
    return request("/billing/transactions");
  }
};
