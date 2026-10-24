<script setup>
// Nombre de la aldea que se mira, arriba a la izquierda. Al pulsarlo se elige otra aldea. Mientras
// la segunda no existe, se cuenta cuándo nacerá.
import { onBeforeUnmount, onMounted, ref } from "vue";
import Icono from "./Icono.vue";
import { cambiarAldea, ir, ruta } from "../ruta.js";

defineProps({ nombre: String });
const abierto = ref(false);
const TIPO = { aldea: "Aldea", pueblo: "Pueblo", villa: "Villa", ciudad: "Ciudad" };
const aldeas = ref([]);

async function cargar() {
  try {
    const r = await fetch("/api/aldeas");
    if (r.ok) aldeas.value = await r.json();
  } catch { /* se vuelve a intentar al abrir */ }
}
let reloj;
onMounted(() => { cargar(); reloj = setInterval(cargar, 60000); });
onBeforeUnmount(() => clearInterval(reloj));

function elegir(a) {
  abierto.value = false;
  if (a.existe && a.id !== ruta.aldea) cambiarAldea(a.id);
}
</script>

<template>
  <div class="selector">
    <button type="button" class="actual" :aria-expanded="abierto" aria-haspopup="listbox" @click="abierto = !abierto; cargar()">
      <span class="nombre">{{ nombre || "La aldea" }}</span><Icono nombre="desplegar" :tamano="16" />
    </button>
    <div v-if="abierto" class="lista flotante" role="listbox" aria-label="Aldeas del mundo">
      <p class="titulo">Asentamientos más poblados</p>
      <button v-for="a in aldeas.slice(0, 8)" :key="a.id" type="button" role="option" class="aldea"
              :class="{ on: a.id === ruta.aldea, futura: !a.existe }" :aria-selected="a.id === ruta.aldea"
              :disabled="!a.existe" @click="elegir(a)">
        <strong>{{ a.nombre }}</strong>
        <span v-if="a.existe" class="suave numero">{{ TIPO[a.tipo] ?? "Aldea" }} · {{ a.poblacion.toLocaleString("es-ES") }} habitantes · {{ a.bioma ?? "pradera" }}</span>
        <span v-else class="suave">Todavía no existe. Nacerá cuando la primera aldea llegue a
          {{ a.poblacion_para_fundarla }} habitantes y alguien se marche a fundarla.</span>
      </button>
      <button type="button" class="ver-mundo" @click="abierto = false; ir('mundo')">Ver el mapa del mundo<span v-if="aldeas.length > 8" class="suave"> ({{ aldeas.length }} asentamientos)</span></button>
    </div>
  </div>
</template>

<style scoped>
.selector { position: relative; }
.actual {
  display: inline-flex; align-items: center; gap: var(--space-1); padding: 0; border: none; background: none;
  color: inherit; font: inherit; cursor: pointer;
}
.actual:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 4px; border-radius: var(--radius-sm); }
.nombre {
  font-family: var(--font-pixel); font-size: var(--text-xl); font-weight: 600; letter-spacing: 0.02em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: min(360px, 40vw);   /* «Villa de Mizuno del Norte» no parte la barra */
}
.lista {
  position: absolute; top: calc(100% + 18px); left: calc(-1 * var(--space-4)); z-index: 40; width: 300px;
  display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-2);
}
.titulo { margin: var(--space-1) var(--space-2); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--panel-texto-suave); }
.aldea {
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px; padding: var(--space-2);
  border: none; border-radius: var(--radius-md); background: transparent; color: inherit; font: inherit; text-align: left; cursor: pointer;
}
.aldea:hover:not(:disabled) { background: var(--color-surface-muted); }
.aldea.on {
  border-radius: 0;
  background: var(--active-line) top / 100% 1px no-repeat, var(--active-line) bottom / 100% 1px no-repeat, var(--active-glow);
}
.aldea.futura { cursor: default; opacity: 0.85; }
.ver-mundo {
  margin-top: var(--space-1); padding: var(--space-2); border: none; border-top: 1px solid var(--panel-borde);
  background: transparent; color: inherit; font: inherit; font-size: var(--text-sm); font-weight: 600; text-align: left; cursor: pointer;
}
.ver-mundo:hover { background: var(--color-surface-muted); }
.suave { font-size: var(--text-xs); color: var(--panel-texto-suave); line-height: 1.4; }
</style>
