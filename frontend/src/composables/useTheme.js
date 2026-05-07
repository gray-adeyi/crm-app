import { ref } from "vue";

const isDark = ref(localStorage.getItem("theme") === "dark");

function applyTheme(value) {
  document.documentElement.classList.toggle("dark", value);
  localStorage.setItem("theme", value ? "dark" : "light");
}

if (typeof document !== "undefined") {
  applyTheme(isDark.value);
}

export function useTheme() {
  function toggleTheme() {
    isDark.value = !isDark.value;
    applyTheme(isDark.value);
  }

  return { isDark, toggleTheme };
}
