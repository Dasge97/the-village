<script setup>
// Novedades: cada versión de La aldea con su fecha y lo que cambió, de la más nueva a la más antigua.
import { VERSIONES } from "../versiones.js";
</script>

<template>
  <div class="novedades">
    <p class="intro">La aldea crece poco a poco. Aquí queda apuntado cada cambio, para ver cómo ha ido evolucionando.</p>
    <ol class="versiones">
      <li v-for="(v, i) in VERSIONES" :key="v.version" class="version" :class="{ actual: i === 0 }">
        <span class="marca" aria-hidden="true"></span>
        <div class="contenido">
          <p class="cabecera">
            <span class="numero etiqueta">v{{ v.version }}</span>
            <strong>{{ v.titulo }}</strong>
            <span v-if="i === 0" class="actual-texto">Ahora</span>
          </p>
          <p class="fecha numero">{{ v.fecha }}</p>
          <ul>
            <li v-for="c in v.cambios" :key="c">{{ c }}</li>
          </ul>
        </div>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.novedades { display: flex; flex-direction: column; gap: var(--space-4); }
.intro { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.versiones { list-style: none; margin: 0; padding: 0; }
.version { position: relative; display: grid; grid-template-columns: 16px 1fr; gap: var(--space-3); padding-bottom: var(--space-6); }
.version:not(:last-child)::before { content: ""; position: absolute; left: 7px; top: 20px; bottom: 0; width: 2px; background: var(--color-border); }
.marca { width: 16px; height: 16px; margin-top: 3px; border-radius: 50%; border: 2px solid var(--color-border-strong); background: var(--panel-bg); }
.actual .marca { border-color: var(--color-accent); background: var(--color-accent); }
.contenido { min-width: 0; }
.cabecera { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); margin: 0; }
.etiqueta { padding: 0 6px; border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 600; background: var(--color-surface-muted); }
.actual-texto { font-size: var(--text-xs); font-weight: 600; color: var(--color-accent); }
.fecha { margin: 2px 0 var(--space-2); font-size: var(--text-xs); color: var(--color-text-muted); }
ul { margin: 0; padding-left: var(--space-4); display: flex; flex-direction: column; gap: var(--space-1); font-size: var(--text-sm); line-height: 1.5; }
</style>
