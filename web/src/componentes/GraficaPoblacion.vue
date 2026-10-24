<script setup>
// Población al final de cada año. Una sola serie: línea de 2 px, relleno muy suave, punto final
// con su valor, cuadrícula fina y una línea vertical que sigue al puntero con el dato del año.
// Con `maximo` a 0, la escala se ajusta sola a los datos. Cada resumen puede traer `detalle`: líneas
// de más para el globo (la gente de cada tipo de asentamiento, en el mapa del mundo).
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({ resumenes: Array, maximo: { type: Number, default: 20 }, unidad: { type: String, default: "habitantes" } });
const numero = (n) => n.toLocaleString("es-ES");

const caja = ref(null);
const ancho = ref(600);
const ALTO = 240;

const sobre = ref(null);
let observador;

onMounted(() => {
  observador = new ResizeObserver(() => { ancho.value = caja.value.clientWidth; });
  observador.observe(caja.value);
});
onBeforeUnmount(() => observador?.disconnect());

const puntos = computed(() => props.resumenes.map((r) => ({ ano: r.ano, valor: r.poblacion, detalle: r.detalle ?? [] })));
// Tope de la escala y cinco marcas redondas: 1, 2 o 5 por una potencia de diez.
const tope = computed(() => {
  if (props.maximo) return props.maximo;
  const mayor = Math.max(4, ...puntos.value.map((p) => p.valor));
  const paso = [1, 2, 5].map((f) => f * 10 ** Math.floor(Math.log10(mayor / 4))).find((p) => p * 4 >= mayor) ?? 10 ** Math.ceil(Math.log10(mayor / 4));
  return paso * 4;
});
const marcas = computed(() => [0, 1, 2, 3, 4].map((i) => (tope.value / 4) * i));
const M = computed(() => ({ izq: 16 + 7 * numero(tope.value).length, der: 16 + 7 * numero(puntos.value.at(-1)?.valor ?? 0).length, arr: 16, aba: 28 }));
const escala = computed(() => {
  const n = puntos.value.length;
  const { izq, der, arr, aba } = M.value;
  const w = ancho.value - izq - der;
  const h = ALTO - arr - aba;
  const x = (i) => izq + (n <= 1 ? w / 2 : (i / (n - 1)) * w);
  const y = (v) => arr + h - (v / tope.value) * h;
  return { x, y, w, h };
});
const linea = computed(() => puntos.value.map((p, i) => `${i ? "L" : "M"}${escala.value.x(i)},${escala.value.y(p.valor)}`).join(" "));
const area = computed(() => {
  if (!puntos.value.length) return "";
  const { x, y } = escala.value;
  const n = puntos.value.length;
  return `${linea.value} L${x(n - 1)},${y(0)} L${x(0)},${y(0)} Z`;
});
// Etiquetas de años: unas seis repartidas, siempre números enteros.
const anos = computed(() => {
  const n = puntos.value.length;
  const cada = Math.max(1, Math.ceil(n / 6));
  return puntos.value.map((p, i) => ({ ...p, i })).filter((p) => p.i % cada === 0 || p.i === n - 1);
});

function mover(e) {
  const n = puntos.value.length;
  if (!n) return;
  const caja2 = e.currentTarget.getBoundingClientRect();
  const px = e.clientX - caja2.left;
  const i = n <= 1 ? 0 : Math.round(((px - M.value.izq) / escala.value.w) * (n - 1));
  sobre.value = Math.max(0, Math.min(n - 1, i));
}
const ultimo = computed(() => puntos.value[puntos.value.length - 1]);
</script>

<template>
  <div ref="caja" class="grafica">
    <svg :width="ancho" :height="ALTO" role="img"
         :aria-label="`Población al final de cada año. Último año: ${numero(ultimo?.valor ?? 0)} ${unidad}.`"
         @pointermove="mover" @pointerleave="sobre = null">
      <g class="rejilla">
        <line v-for="v in marcas" :key="v" :x1="M.izq" :x2="ancho - M.der" :y1="escala.y(v)" :y2="escala.y(v)" />
      </g>
      <g class="ejes">
        <text v-for="v in marcas" :key="'y' + v" :x="M.izq - 8" :y="escala.y(v) + 4" text-anchor="end">{{ numero(v) }}</text>
        <text v-for="a in anos" :key="'x' + a.ano" :x="escala.x(a.i)" :y="ALTO - 8" text-anchor="middle">{{ a.ano }}</text>
      </g>
      <path class="area" :d="area" />
      <path class="linea" :d="linea" />
      <template v-if="ultimo">
        <circle class="punto" :cx="escala.x(puntos.length - 1)" :cy="escala.y(ultimo.valor)" r="4" />
        <text class="valor" :x="escala.x(puntos.length - 1) + 10" :y="escala.y(ultimo.valor) + 4">{{ numero(ultimo.valor) }}</text>
      </template>
      <template v-if="sobre !== null">
        <line class="cruz" :x1="escala.x(sobre)" :x2="escala.x(sobre)" :y1="M.arr" :y2="ALTO - M.aba" />
        <circle class="punto" :cx="escala.x(sobre)" :cy="escala.y(puntos[sobre].valor)" r="4" />
      </template>
    </svg>
    <div v-if="sobre !== null" class="globo" :style="{ left: Math.min(escala.x(sobre) + 12, ancho - 190) + 'px' }">
      <strong>Año {{ puntos[sobre].ano }}</strong>
      <span class="numero">{{ numero(puntos[sobre].valor) }} {{ unidad }}</span>
      <span v-for="d in puntos[sobre].detalle" :key="d" class="detalle numero">{{ d }}</span>
    </div>
  </div>
</template>

<style scoped>
.grafica { position: relative; width: 100%; }
svg { display: block; touch-action: pan-y; }
.rejilla line { stroke: var(--color-border); stroke-width: 1; }
.ejes text { fill: var(--color-text-muted); font-size: 12px; font-variant-numeric: tabular-nums; }
.area { fill: var(--color-primary); opacity: 0.1; }
.linea { fill: none; stroke: var(--color-primary); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.punto { fill: var(--color-primary); stroke: var(--color-surface); stroke-width: 2; }
.valor { fill: var(--color-text); font-size: 12px; font-weight: 600; font-variant-numeric: tabular-nums; }
.cruz { stroke: var(--color-text-muted); stroke-width: 1; }
.globo {
  position: absolute; top: 8px; pointer-events: none;
  display: flex; flex-direction: column; padding: var(--space-2) var(--space-3);
  background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md);
  box-shadow: var(--shadow-2); font-size: var(--text-sm);
}
.detalle { font-size: var(--text-xs); color: var(--color-text-muted); }
</style>
