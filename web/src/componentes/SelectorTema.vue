<script setup>
import { ref } from "vue";

const OPCIONES = [
  { valor: "light", texto: "Claro" },
  { valor: "system", texto: "Sistema" },
  { valor: "dark", texto: "Oscuro" },
];

const leer = () => { try { return localStorage.getItem("tema") || "system"; } catch { return "system"; } };
const tema = ref(leer());

function elegir(valor) {
  tema.value = valor;
  if (valor === "system") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = valor;
  try { localStorage.setItem("tema", valor); } catch {}
}
</script>

<template>
  <div class="selector" role="radiogroup" aria-label="Tema de colores">
    <button v-for="o in OPCIONES" :key="o.valor" type="button" role="radio"
            :aria-checked="tema === o.valor" :class="{ on: tema === o.valor }" @click="elegir(o.valor)">
      {{ o.texto }}
    </button>
  </div>
</template>

<style scoped>
.selector { display: flex; gap: var(--space-1); }
button {
  height: var(--control-height);
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
  transition: color var(--duration) var(--ease), background-color var(--duration) var(--ease);
}
button:hover { color: var(--color-text); background: var(--color-surface-muted); }
button:active { background: var(--color-border); }
button.on { color: var(--color-text); font-weight: 600; border-radius: 0; background: var(--active-line) bottom / 100% 2px no-repeat; }
@media (max-width: 640px) { button { height: 44px; padding: 0 var(--space-2); } }
</style>
