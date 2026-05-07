import { getActivePinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";

import AnalyticsPage from "../pages/AnalyticsPage.vue";
import BillingPage from "../pages/BillingPage.vue";
import CustomersPage from "../pages/CustomersPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import OnboardingPage from "../pages/OnboardingPage.vue";
import OrdersPage from "../pages/OrdersPage.vue";
import InventoryPage from "../pages/InventoryPage.vue";
import SettingsPage from "../pages/SettingsPage.vue";
import SignupPage from "../pages/SignupPage.vue";
import VerifyEmailPage from "../pages/VerifyEmailPage.vue";
import { isAuthenticated } from "../services/auth";
import { useSessionStore } from "../stores/session";

const NotificationsPage = () => import("../pages/NotificationsPage.vue");
const ReportsPage = () => import("../pages/ReportsPage.vue");

const routes = [
  { path: "/login", name: "login", component: LoginPage, meta: { guestOnly: true } },
  { path: "/signup", name: "signup", component: SignupPage, meta: { guestOnly: true } },
  { path: "/verify-email", name: "verify-email", component: VerifyEmailPage, meta: { guestOnly: true } },
  { path: "/", name: "dashboard", component: DashboardPage, meta: { requiresAuth: true } },
  { path: "/customers", name: "customers", component: CustomersPage, meta: { requiresAuth: true } },
  { path: "/orders", name: "orders", component: OrdersPage, meta: { requiresAuth: true } },
  { path: "/inventory", name: "inventory", component: InventoryPage, meta: { requiresAuth: true } },
  { path: "/analytics", name: "analytics", component: AnalyticsPage, meta: { requiresAuth: true } },
  { path: "/billing", name: "billing", component: BillingPage, meta: { requiresAuth: true } },
  { path: "/billing/success", name: "billing-success", component: BillingPage, meta: { requiresAuth: true } },
  { path: "/billing/failed", name: "billing-failed", component: BillingPage, meta: { requiresAuth: true } },
  { path: "/settings", name: "settings", component: SettingsPage, meta: { requiresAuth: true } },
  { path: "/reports", name: "reports", component: ReportsPage, meta: { requiresAuth: true } },
  { path: "/notifications", name: "notifications", component: NotificationsPage, meta: { requiresAuth: true } },
  { path: "/onboarding", name: "onboarding", component: OnboardingPage, meta: { requiresAuth: true } }
];

const SUBSCRIPTION_BYPASS = new Set(["billing", "billing-success", "billing-failed", "settings", "onboarding", "login", "signup", "verify-email"]);

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) return { name: "login" };
  if (to.meta.guestOnly && isAuthenticated()) return { name: "dashboard" };

  if (to.meta.requiresAuth && isAuthenticated()) {
    const pinia = getActivePinia();
    if (pinia) {
      const session = useSessionStore(pinia);
      if (!session.initialized) {
        await session.loadUser();
      }
      if (!isAuthenticated()) return { name: "login" };
      if (session.user?.needs_subscription_upgrade && !SUBSCRIPTION_BYPASS.has(to.name)) {
        return { name: "billing" };
      }
    }
  }

  return true;
});

export default router;
