<script setup>
// Historia año a año: cifras de todos los años, gráfica de población y tabla con un resumen por año.
import { computed, onMounted, ref, watch } from "vue";
import Cifra from "./Cifra.vue";
import GraficaPoblacion from "./GraficaPoblacion.vue";
import { api } from "../ruta.js";

const props = defineProps({ ano: Number });

const resumenes = ref([]);
const fase = ref("cargando");

async function cargar() {
  try {
    const r = await fetch(api("/api/resumenes"));
    if (!r.ok) throw new Error();
    resumenes.value = await r.json();
    fase.value = "datos";
  } catch {
    if (fase.value !== "datos") fase.value = "error";
  }
}
onMounted(cargar);
watch(() => props.ano, cargar);   // cada año nuevo trae un resumen nuevo

const muertes = (r) => Object.values(r.muertes).reduce((a, b) => a + b, 0);
const filas = computed(() => [...resumenes.value].reverse());
const totales = computed(() => ({
  nacimientos: resumenes.value.reduce((s, r) => s + r.nacimientos, 0),
  muertes: resumenes.value.reduce((s, r) => s + muertes(r), 0),
  parejas: resumenes.value.reduce((s, r) => s + r.parejas, 0),
}));
</script>

<template>
  <div class="anual">
    <h3>Año a año</h3>
    <p class="intro">Cómo ha cambiado la aldea año a año. Cada año del mundo dura un día real.</p>

    <div v-if="fase === 'cargando'" class="esqueleto" style="height: 320px"></div>
    <p v-else-if="fase === 'error'" class="tarjeta vacia">No hemos podido cargar la historia. Recarga la página en unos segundos.</p>
    <p v-else-if="!resumenes.length" class="tarjeta vacia">
      La aldea todavía no ha cumplido su primer año. El primer resumen aparecerá aquí al acabar el invierno, dentro de menos de un día.
    </p>

    <template v-else>
      <div class="cifras">
        <Cifra etiqueta="Años vividos" :valor="resumenes.length" />
        <Cifra etiqueta="Nacimientos" :valor="totales.nacimientos" />
        <Cifra etiqueta="Muertes" :valor="totales.muertes" />
        <Cifra etiqueta="Parejas formadas" :valor="totales.parejas" />
      </div>

      <section class="tarjeta">
        <h4 class="tarjeta-titulo">Habitantes al final de cada año</h4>
        <GraficaPoblacion :resumenes="resumenes" />
      </section>

      <section class="tarjeta">
        <h4 class="tarjeta-titulo">Resumen de cada año</h4>
        <div class="desplazable">
          <table>
            <thead>
              <tr>
                <th scope="col">Año</th><th scope="col">Habitantes</th><th scope="col">Nacimientos</th>
                <th scope="col">Muertes</th><th scope="col">Parejas</th><th scope="col">Llegadas</th>
                <th scope="col">Marchas</th><th scope="col">Ataques</th><th scope="col">Comida producida</th>
                <th scope="col">Casas</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in filas" :key="r.ano">
                <th scope="row">{{ r.ano }}</th><td>{{ r.poblacion }}</td><td>{{ r.nacimientos }}</td>
                <td>{{ muertes(r) }}</td><td>{{ r.parejas }}</td><td>{{ r.llegadas }}</td>
                <td>{{ r.marchas }}</td><td>{{ r.ataques }}</td><td>{{ r.producido.comida ?? 0 }}</td>
                <td>{{ r.casas }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.anual { display: flex; flex-direction: column; gap: var(--space-4); min-width: 0; }
h3 { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.intro { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.cifras { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--space-3); }
.desplazable { overflow: auto; max-height: 480px; }
table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); font-variant-numeric: tabular-nums; }
th, td { padding: var(--space-2) var(--space-3); text-align: right; white-space: nowrap; border-bottom: 1px solid var(--color-border); }
thead th { position: sticky; top: 0; background: var(--color-surface); color: var(--color-text-muted); font-weight: 600; }
th:first-child { text-align: left; }
tbody tr:hover { background: var(--color-surface-muted); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
</style>
