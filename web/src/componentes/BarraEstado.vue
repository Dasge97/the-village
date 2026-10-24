<script setup>
// Barra fina de abajo del todo: la versión actual, el acceso a las novedades y al panel de
// administración. Discreta a propósito.
import Icono from "./Icono.vue";
import { ACTUAL } from "../versiones.js";
import { ir, ruta } from "../ruta.js";

defineProps({ conectado: Boolean });
</script>

<template>
  <footer class="estado">
    <span class="punto" :class="{ cortado: !conectado }" aria-hidden="true"></span>
    <span>{{ conectado ? "Conectado" : "Reconectando" }}</span>
    <span class="separador" aria-hidden="true">·</span>
    <button type="button" class="version" :aria-current="ruta.panel === 'admin' ? 'page' : undefined"
            title="Panel de administración" aria-label="Administración" @click="ir(ruta.panel === 'admin' ? null : 'admin')">
      <Icono nombre="candado" :tamano="12" /><span class="largo">Administración</span>
    </button>
    <span class="separador" aria-hidden="true">·</span>
    <button type="button" class="version" :aria-current="ruta.panel === 'novedades' ? 'page' : undefined"
            title="Ver los cambios de cada versión" @click="ir(ruta.panel === 'novedades' ? null : 'novedades')">
      <Icono nombre="chispa" :tamano="12" /><span class="largo">Versión {{ ACTUAL.version }} · {{ ACTUAL.titulo }}</span><span class="corto">v{{ ACTUAL.version }} · Novedades</span>
    </button>
  </footer>
</template>

<style scoped>
.estado {
  position: absolute; left: 0; right: 0; bottom: 0; z-index: 25; height: var(--alto-estado);
  display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); padding: 0 var(--space-4);
  font-size: var(--text-xs); color: var(--panel-texto-suave);
  background: color-mix(in srgb, var(--panel-bg) 85%, transparent); border-top: 1px solid var(--panel-borde);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
}
.punto { width: 6px; height: 6px; border-radius: 50%; background: var(--success); }
.punto.cortado { background: var(--warning); }
.separador { opacity: 0.6; }
.version {
  display: inline-flex; align-items: center; gap: var(--space-1); height: 100%; padding: 0 var(--space-1);
  border: none; background: none; color: inherit; font: inherit; cursor: pointer;
}
.version:hover, .version[aria-current] { color: var(--panel-texto); text-decoration: underline; text-underline-offset: 2px; }
.estado { white-space: nowrap; }
.corto { display: none; }
@media (max-width: 600px) { .largo { display: none; } .corto { display: inline; } }
.version:focus-visible { outline: 2px solid var(--color-focus); outline-offset: -2px; border-radius: var(--radius-sm); }
</style>
