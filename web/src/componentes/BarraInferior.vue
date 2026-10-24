<script setup>
// Pestañas fijas de abajo en el móvil. Qué es La aldea va en el menú de arriba.
import Icono from "./Icono.vue";
import { ir, ruta } from "../ruta.js";

const PESTANAS = [
  { panel: null, texto: "Mapa", icono: "mapa" },
  { panel: "habitantes", texto: "Habitantes", icono: "personas" },
  { panel: "historia", texto: "Historia", icono: "historial" },
  { panel: "familias", texto: "Linajes", icono: "familia" },
];
</script>

<template>
  <nav class="inferior flotante" aria-label="Secciones">
    <button v-for="p in PESTANAS" :key="p.texto" type="button" :class="{ on: ruta.panel === p.panel }"
            :aria-current="ruta.panel === p.panel ? 'page' : undefined" @click="ir(p.panel)">
      <Icono :nombre="p.icono" :tamano="22" /><span>{{ p.texto }}</span>
    </button>
  </nav>
</template>

<style scoped>
.inferior {
  position: absolute; left: var(--space-2); right: var(--space-2); bottom: calc(var(--space-2) + var(--alto-estado)); z-index: 20;
  display: grid; grid-template-columns: repeat(4, 1fr); height: 60px; padding: var(--space-1);
}
button {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
  border: none; border-radius: var(--radius-md); background: transparent; color: var(--panel-texto-suave);
  font: inherit; font-size: var(--text-xs); cursor: pointer;
}
button.on { color: var(--color-accent); font-weight: 600; background: var(--active-line) bottom / 70% 2px no-repeat; }
</style>
