<script setup>
import Chart from "chart.js/auto";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  label: { type: String, default: "Orders / units" },
  color: { type: String, default: "#6366f1" },
  stacked: { type: Boolean, default: false },
  horizontal: { type: Boolean, default: false },
  currencyFormat: { type: Boolean, default: false }
});

const canvasRef = ref(null);
let chart;

function colors() {
  const base = props.color || "#6366f1";
  return props.values.map(() => `${base}b3`);
}

function build() {
  if (!canvasRef.value) return;
  chart?.destroy();
  const type = props.horizontal ? "bar" : "bar";
  chart = new Chart(canvasRef.value, {
    type,
    data: {
      labels: [...props.labels],
      datasets: [
        {
          label: props.label,
          data: [...props.values],
          backgroundColor: colors(),
          borderRadius: 6,
          barThickness: props.horizontal ? 18 : undefined
        }
      ]
    },
    options: {
      indexAxis: props.horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: props.stacked,
          ticks: props.currencyFormat
            ? {
                callback: (v) => "₦" + Number(v).toLocaleString()
              }
            : {}
        },
        y: {
          stacked: props.stacked,
          beginAtZero: true,
          ticks: props.currencyFormat
            ? {
                callback: (v) => "₦" + Number(v).toLocaleString()
              }
            : {}
        }
      },
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = Number(ctx.raw || 0);
              return props.currencyFormat ? `${ctx.dataset.label}: ₦${v.toLocaleString()}` : `${ctx.dataset.label}: ${v}`;
            }
          }
        }
      }
    }
  });
}

onMounted(build);
watch(
  () => [props.labels, props.values, props.label, props.currencyFormat, props.horizontal],
  () => build(),
  { deep: true }
);
onBeforeUnmount(() => chart?.destroy());
</script>

<template>
  <div class="h-64 w-full md:h-72">
    <canvas ref="canvasRef" />
  </div>
</template>
