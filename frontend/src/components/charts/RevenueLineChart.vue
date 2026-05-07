<script setup>
import Chart from "chart.js/auto";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  label: { type: String, default: "Collected (₦)" },
  currencyFormat: { type: Boolean, default: true }
});

const canvasRef = ref(null);
let chart;

function build() {
  if (!canvasRef.value) return;
  chart?.destroy();
  chart = new Chart(canvasRef.value, {
    type: "line",
    data: {
      labels: [...props.labels],
      datasets: [
        {
          label: props.label,
          data: [...props.values],
          borderColor: "#6366f1",
          backgroundColor: "rgba(99,102,241,0.15)",
          fill: true,
          tension: 0.35,
          pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          ticks: {
            callback: (v) => (props.currencyFormat ? "₦" + Number(v).toLocaleString() : Number(v).toLocaleString())
          }
        }
      },
      plugins: { legend: { display: true } }
    }
  });
}

onMounted(build);
watch(
  () => [props.labels, props.values, props.label, props.currencyFormat],
  () => build(),
  { deep: true }
);
onBeforeUnmount(() => chart?.destroy());
</script>

<template>
  <div class="h-64 w-full">
    <canvas ref="canvasRef" />
  </div>
</template>
