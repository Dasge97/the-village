<script setup>
// Columna de iconos de la izquierda (escritorio). Cada icono abre su panel; pulsarlo otra vez lo cierra.
// "Qué es La aldea" va abajo, separado de las secciones de la aldea.
import Icono from "./Icono.vue";
import { PANELES, ir, ruta } from "../ruta.js";
</script>

<template>
  <nav class="riel flotante" aria-label="Secciones">
    <button v-for="p in PANELES.filter((x) => !x.oculto)" :key="p.id" type="button" class="boton-icono" :class="{ on: ruta.panel === p.id, aparte: p.id === 'info' }"
            :aria-label="p.texto" :aria-current="ruta.panel === p.id ? 'page' : undefined" :title="p.texto"
            @click="ir(ruta.panel === p.id ? null : p.id)">
      <Icono :nombre="p.icono" :tamano="22" />
    </button>
  </nav>
</template>

<style scoped>
.riel {
  position: absolute; left: var(--space-4); top: 84px; z-index: 20;
  display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-2);
  border-radius: var(--radius-lg);
}
.boton-icono { width: 48px; height: 48px; }
.aparte { position: relative; margin-top: var(--space-2); }
.aparte::before {
  content: ""; position: absolute; top: calc(-1 * var(--space-2) - 1px); left: var(--space-2); right: var(--space-2);
  height: 1px; background: var(--panel-borde);
}
</style>
