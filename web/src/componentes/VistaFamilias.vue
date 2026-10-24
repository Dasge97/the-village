<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import Cara from "./Cara.vue";
import Cifra from "./Cifra.vue";
import VidaPersona from "./VidaPersona.vue";
import { NODO, calcularArbol, descendientesVivos, familiaDe } from "../arbol.js";
import { api, ir, ruta } from "../ruta.js";
import { CAUSA, LLEGADA, anoDelTurno, mayuscula } from "../textos.js";

const props = defineProps({ turno: Number });

const datos = ref(null);
const fase = ref("cargando");
const caja = ref(null);

async function cargar() {
  try {
    const r = await fetch(api("/api/arbol"));
    if (!r.ok) throw new Error();
    datos.value = await r.json();
    fase.value = "datos";
  } catch {
    if (!datos.value) fase.value = "error";
  }
}
onMounted(cargar);
// El árbol cambia poco: se recarga cada 30 turnos (5 minutos reales).
watch(() => props.turno, (t, antes) => { if (Math.floor(t / 30) !== Math.floor((antes ?? 0) / 30)) cargar(); });

const arbol = computed(() => (datos.value ? calcularArbol(datos.value.personas) : null));
const porId = computed(() => arbol.value?.nodoDe ?? new Map());
const elegido = computed(() => (ruta.id ? porId.value.get(ruta.id) ?? null : null));
const resaltados = computed(() => (elegido.value ? familiaDe(elegido.value.id, porId.value) : null));

const resumen = computed(() => {
  if (!arbol.value) return null;
  const personas = arbol.value.nodos;
  const raices = personas.filter((p) => !p.padres.length);
  let mejor = null;
  for (const r of raices) {
    const n = descendientesVivos(r.id, porId.value);
    if (!mejor || n > mejor.n) mejor = { persona: r, n };
  }
  return { total: personas.length, vivos: personas.filter((p) => p.vivo).length, generaciones: arbol.value.generaciones, mejor };
});

// Texto corto bajo el nombre: la edad si vive, o los años en que vivió en la aldea.
function vida(p) {
  if (p.vivo) return `${p.edad} años`;
  if (p.llegada === "fundador") return `† año ${anoDelTurno(p.salida)}`;
  return `años ${Math.max(1, anoDelTurno(p.nacimiento))}–${anoDelTurno(p.salida)}`;
}

function elegir(id) { ir("familias", id); }

// Al elegir a alguien, el árbol se desplaza hasta esa persona.
watch(elegido, async (p) => {
  if (!p || !caja.value) return;
  await nextTick();
  caja.value.scrollTo({ left: p.x - caja.value.clientWidth / 2 + NODO.ancho / 2, top: p.y - caja.value.clientHeight / 2, behavior: "smooth" });
});

const nombre = (id) => porId.value.get(id);
</script>

<template>
  <div class="vista">
    <div class="titulo">
      <p>Todas las personas que han vivido en la aldea, desde los fundadores. Pulsa a alguien para ver de quién viene y quién viene de él.</p>
    </div>

    <div v-if="resumen" class="cifras">
      <Cifra etiqueta="Han vivido aquí" :valor="resumen.total" />
      <Cifra etiqueta="Viven ahora" :valor="resumen.vivos" />
      <Cifra etiqueta="Generaciones" :valor="resumen.generaciones" />
      <Cifra v-if="resumen.mejor" class="ancha" etiqueta="Familia con más descendientes vivos"
             :valor="`${resumen.mejor.persona.nombre} (${resumen.mejor.n})`" />
    </div>

    <div class="cuerpo">
      <section ref="caja" class="lienzo tarjeta" aria-label="Árbol genealógico">
        <div v-if="fase === 'cargando'" class="esqueleto" style="height: 100%"></div>
        <p v-else-if="fase === 'error'" class="vacia">No hemos podido cargar el árbol. Recarga la página en unos segundos.</p>
        <div v-else class="arbol" :style="{ width: arbol.ancho + 'px', height: arbol.alto + 'px' }">
          <svg class="lineas" :width="arbol.ancho" :height="arbol.alto" aria-hidden="true">
            <!-- Parejas: un arco por encima de la fila, para no cruzar a quien esté entre los dos. -->
            <path v-for="(l, i) in arbol.parejas" :key="'p' + i" class="pareja"
                  :d="`M${l.desde.x + NODO.ancho / 2},${l.desde.y} C${l.desde.x + NODO.ancho / 2},${l.desde.y - 22} ${l.hasta.x + NODO.ancho / 2},${l.hasta.y - 22} ${l.hasta.x + NODO.ancho / 2},${l.hasta.y}`"
                  :class="{ tenue: resaltados && !(resaltados.has(l.desde.id) && resaltados.has(l.hasta.id)) }" />
            <path v-for="l in arbol.hijos" :key="'h' + l.hijo.id"
                  :d="`M${l.x1},${l.y1} V${(l.y1 + l.y2) / 2} H${l.x2} V${l.y2}`"
                  :class="{ tenue: resaltados && !resaltados.has(l.hijo.id) }" />
          </svg>
          <button v-for="n in arbol.nodos" :key="n.id" type="button" class="nodo"
                  :class="{ muerto: !n.vivo, tenue: resaltados && !resaltados.has(n.id), elegido: elegido?.id === n.id }"
                  :style="{ left: n.x + 'px', top: n.y + 'px', width: NODO.ancho + 'px', height: NODO.alto + 'px' }"
                  @click="elegir(n.id)">
            <Cara :personaje="n.personaje" :nombre="n.nombre" :vivo="n.vivo" :tamano="32" />
            <span class="texto"><span class="nombre">{{ n.nombre }}</span><span class="suave numero">{{ vida(n) }}</span></span>
          </button>
        </div>
      </section>

      <aside class="detalle tarjeta">
        <template v-if="!elegido">
          <p class="vacia">Elige a una persona del árbol para ver su historia, su familia y cuántos descendientes vivos tiene.</p>
          <div class="leyenda">
            <h3>Cómo se lee el árbol</h3>
            <p><span class="muestra linea-pareja"></span>Pareja</p>
            <p><span class="muestra linea-hijos"></span>De padres a hijos</p>
            <p><span class="muestra nodo-vivo"></span>Vive en la aldea</p>
            <p><span class="muestra nodo-muerto"></span>Ya no vive en la aldea</p>
            <p class="vacia">Cada fila es una generación. Los fundadores están arriba.</p>
          </div>
        </template>
        <template v-else>
          <div class="cabecera">
            <Cara :personaje="elegido.personaje" :nombre="elegido.nombre" :vivo="elegido.vivo" :tamano="64" />
            <div>
              <h2>{{ elegido.nombre }}</h2>
              <p class="suave">{{ LLEGADA[elegido.llegada](elegido.sexo) }}<template v-if="elegido.oficio"> · {{ mayuscula(elegido.oficio) }}</template></p>
              <p v-if="elegido.vivo" class="suave">Vive en la aldea, tiene {{ elegido.edad }} años.</p>
              <p v-else class="suave">{{ mayuscula(CAUSA[elegido.causa]) }} en el año {{ anoDelTurno(elegido.salida) }}.</p>
            </div>
          </div>
          <button v-if="elegido.vivo" type="button" class="boton" @click="ir('habitantes', elegido.id)">Ver en la aldea</button>
          <dl class="familia">
            <template v-for="[titulo, ids] in [['Padres', elegido.padres], ['Parejas', elegido.parejas], ['Hijos', elegido.hijos]]" :key="titulo">
              <dt>{{ titulo }}</dt>
              <dd>
                <span v-if="!ids.length" class="suave">Nadie</span>
                <button v-for="i in ids" :key="i" type="button" class="persona" @click="elegir(i)">
                  <Cara :personaje="nombre(i).personaje" :nombre="nombre(i).nombre" :vivo="nombre(i).vivo" :tamano="24" />{{ nombre(i).nombre }}
                </button>
              </dd>
            </template>
            <dt>Descendientes vivos</dt>
            <dd class="numero">{{ descendientesVivos(elegido.id, porId) }}</dd>
          </dl>
          <h3 class="titulo-vida">Su vida</h3>
          <VidaPersona :vida="elegido.vida" />
        </template>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.vista { display: flex; flex-direction: column; gap: var(--space-4); height: 100%; min-height: 0; }
.titulo h1 { font-size: var(--text-2xl); }
.titulo p { margin: 0; color: var(--color-text-muted); max-width: 720px; }
.cifras { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--space-3); }
.ancha { grid-column: span 2; }
.cuerpo { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: var(--space-4); flex: 1; min-height: 0; }
.lienzo { overflow: auto; padding: var(--space-8) var(--space-6) var(--space-6); min-height: 420px; }
.arbol { position: relative; }
.lineas { position: absolute; inset: 0; overflow: visible; }
.lineas path { fill: none; stroke: var(--color-border-strong); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; transition: opacity var(--duration) var(--ease); }
.lineas .pareja { stroke: var(--primary-400); }
.tenue { opacity: 0.25; }
.nodo {
  position: absolute; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-2);
  border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface);
  color: var(--color-text); font: inherit; text-align: left; cursor: pointer;
  transition: opacity var(--duration) var(--ease), border-color var(--duration) var(--ease);
}
.nodo:hover { border-color: var(--color-border-strong); }
.nodo.muerto { background: var(--color-surface-muted); }
.nodo.elegido { border: 2px solid var(--color-primary); }
.texto { display: flex; flex-direction: column; min-width: 0; }
.nombre { font-size: var(--text-sm); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.suave { color: var(--color-text-muted); font-size: var(--text-xs); margin: 0; }
.detalle { display: flex; flex-direction: column; gap: var(--space-4); overflow-y: auto; }
.detalle .cabecera { display: flex; gap: var(--space-4); align-items: center; }
.detalle h2 { font-size: var(--text-xl); }
.detalle .suave { font-size: var(--text-sm); margin-top: var(--space-1); }
.boton {
  height: var(--control-height); border-radius: var(--radius-md); border: none;
  background: var(--color-primary); color: var(--color-on-primary);
  font: inherit; font-size: var(--text-sm); font-weight: 600; cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.boton:hover { background: var(--color-primary-hover); }
.familia { display: grid; grid-template-columns: 136px 1fr; gap: var(--space-2); margin: 0; font-size: var(--text-sm); }
.familia dt { color: var(--color-text-muted); padding-top: 4px; }
.familia dd { margin: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; }
.persona {
  display: inline-flex; align-items: center; gap: var(--space-2); padding: 2px var(--space-2) 2px 2px;
  border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface);
  color: var(--color-text); font: inherit; font-size: var(--text-sm); cursor: pointer;
}
.persona:hover { background: var(--color-surface-muted); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.titulo-vida { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); padding-top: var(--space-2); border-top: 1px solid var(--color-border); }
.leyenda { display: flex; flex-direction: column; gap: var(--space-2); padding-top: var(--space-4); border-top: 1px solid var(--color-border); }
.leyenda h3 { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.leyenda p { display: flex; align-items: center; gap: var(--space-3); margin: 0; font-size: var(--text-sm); }
.muestra { flex: none; width: 28px; }
.linea-pareja { height: 2px; background: var(--primary-400); }
.linea-hijos { height: 2px; background: var(--color-border-strong); }
.nodo-vivo, .nodo-muerto { height: 18px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface); }
.nodo-muerto { background: var(--color-surface-muted); }
@media (max-width: 960px) {
  .cuerpo { grid-template-columns: 1fr; }
  .lienzo { min-height: 60vh; padding: var(--space-4); }
}
</style>
