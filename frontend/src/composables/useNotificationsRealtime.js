/**
 * Notifications transport abstraction — plug in WebSocket / SSE later without changing pages.
 *
 * Usage:
 *   const { subscribe, dispose } = useNotificationsRealtime(({ type, payload }) => { ... });
 *   subscribe();
 *   onUnmounted(dispose);
 */
import { readonly, ref } from "vue";

export function useNotificationsRealtime(onEvent) {
  const connected = ref(false);
  const transportId = ref("polling-ready");

  function subscribe() {
    connected.value = true;
    transportId.value = "polling-ready";
    return () => dispose();
  }

  function dispose() {
    connected.value = false;
  }

  return {
    connected: readonly(connected),
    transportId: readonly(transportId),
    subscribe,
    dispose,
  };
}
