<script setup>
import Chart from "chart.js/auto";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  pending: { type: Number, default: 0 },
  partial: { type: Number, default: 0 },
  paid: { type: Number, default: 0 }
});

const canvasRef = ref(null);
let chart;

function build() {
  if (!canvasRef.value) return;
  chart?.destroy();
  chart = new Chart(canvasRef.value, {
    type: "bar",
    data: {
      labels: ["Pending", "Partial", "Paid"],
      datasets: [
        {
          label: "Orders",
          data: [props.pending, props.partial, props.paid],
          backgroundColor: ["#fbbf24", "#38bdf8", "#34d399"]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

onMounted(build);
watch(() => [props.pending, props.partial, props.paid], build);
onBeforeUnmount(() => chart?.destroy());
</script>

<template>
  <div class="h-56 w-full">
    <canvas ref="canvasRef" />
  </div>
</template>
