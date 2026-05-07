import { ref } from "vue";

const toasts = ref([]);

let seq = 0;

function remove(id) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

export function useToast() {
  function push(type, message, title = "") {
    const id = ++seq;
    toasts.value = [...toasts.value, { id, type, message, title }];
    window.setTimeout(() => remove(id), 4500);
    return id;
  }

  return {
    toasts,
    success: (message, title) => push("success", message, title),
    error: (message, title) => push("error", message, title),
    info: (message, title) => push("info", message, title),
    remove
  };
}
