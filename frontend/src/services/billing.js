import { api } from "./api";

export const billingService = {
  getPlans: () => api.getBillingPlans(),
  getMe: () => api.getBillingMe(),
  initializeCheckout: (planId) => api.initializeSubscription(planId),
  verifyCheckout: (reference) => api.verifySubscription(reference),
  cancel: (reason) => api.cancelSubscription(reason),
  reactivate: () => api.reactivateSubscription(),
  history: () => api.getBillingTransactions()
};
