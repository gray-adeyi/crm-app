import { createPinia, getActivePinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import "./style.css";
import { setSubscriptionRequiredHandler, setUnauthorizedHandler } from "./services/api";
import { useSessionStore } from "./stores/session";

setUnauthorizedHandler(() => {
  const pinia = getActivePinia();
  if (pinia) {
    useSessionStore(pinia).clearUser();
  }
  router.replace({ name: "login" }).catch(() => {});
});

setSubscriptionRequiredHandler(() => {
  router.replace({ name: "billing" }).catch(() => {});
});

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

app.mount("#app");
