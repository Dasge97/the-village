<script setup>
// Mapa del mundo: las 24 × 24 zonas con su terreno, niebla en las que nadie ha descubierto, los
// caminos y un icono por asentamiento. Se arrastra y se acerca con la rueda o pellizcando; al
// pulsar un asentamiento se entra en él. Al lado, el resumen del mundo en dos subpestañas: los
// asentamientos y la historia (la gente del mundo año a año y sus grandes momentos).
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import Cifra from "./Cifra.vue";
import GraficaPoblacion from "./GraficaPoblacion.vue";
import Subpestanas from "./Subpestanas.vue";
import { cambiarAldea, irPestana, ruta } from "../ruta.js";
import { mayuscula } from "../textos.js";

const datos = ref(null);
const fase = ref("cargando");
const lienzo = ref(null);
const caja = ref(null);

async function cargar() {
  try {
    const r = await fetch("/api/mundo");
    if (!r.ok) throw new Error();
    datos.value = await r.json();
    fase.value = "datos";
    await nextTick();
    dibujar();
  } catch {
    if (!datos.value) fase.value = "error";
  }
}

// Colores de cada terreno y dibujo de cada tipo de asentamiento (recortes de TilesetHouse).
const TERRENO = { pradera: "#8acb4a", bosque: "#4f9436", desierto: "#e9a45a", nieve: "#ecebf2", pantano: "#8d7a5f" };
const ICONO = {
  aldea: [0, 0, 64, 48], pueblo: [256, 0, 48, 48], villa: [304, 0, 64, 48], ciudad: [400, 112, 64, 112],
};
const numero = (n) => n.toLocaleString("es-ES");
// Colores de las líneas de relación sobre el mapa (los caminos son de tierra, #c79a58).
const RELACION = { alianza: "#2f8f5b", tributo: "#e0b030", rivalidad: "#c2412d" };
const TEXTO_TIPO = { aldea: "Aldea", pueblo: "Pueblo", villa: "Villa", ciudad: "Ciudad" };
const casas = new Image();
casas.src = "/sprites/Backgrounds/Tilesets/TilesetHouse.png";
casas.onload = () => dibujar();
// Cada zona se rellena con la hierba lisa de su terreno (de Suelo, como en los mapas de las aldeas).
const HIERBA = { pradera: [0, 192], bosque: [176, 192], desierto: [0, 80], nieve: [0, 304], pantano: [176, 304] };
const suelo = new Image();
suelo.src = "/sprites/Aldea/Suelo.png";
const muestras = {};
suelo.onload = () => {
  for (const [bioma, [x, y]] of Object.entries(HIERBA)) {
    const c = document.createElement("canvas");
    c.width = c.height = 16;
    c.getContext("2d").drawImage(suelo, x, y, 16, 16, 0, 0, 16, 16);
    muestras[bioma] = c;
  }
  dibujar();
};

// Recorta un texto con «…» para que quepa en `ancho` píxeles.
function recortar(g, texto, ancho) {
  if (g.measureText(texto).width <= ancho) return texto;
  while (texto.length > 1 && g.measureText(texto + "…").width > ancho) texto = texto.slice(0, -1);
  return texto + "…";
}

const vista = { zoom: 1, x: 0, y: 0 };    // x, y: zona en el centro de la pantalla
const LADO_ZONA = 56;

function encuadrar() {
  const d = datos.value;
  if (!d?.asentamientos.length) return;
  const xs = d.asentamientos.map((a) => a.zona[0]);
  const ys = d.asentamientos.map((a) => a.zona[1]);
  vista.x = (Math.min(...xs) + Math.max(...xs)) / 2 + 0.5;
  vista.y = (Math.min(...ys) + Math.max(...ys)) / 2 + 0.5;
  const ancho = Math.max(...xs) - Math.min(...xs) + 5;
  const alto = Math.max(...ys) - Math.min(...ys) + 5;
  const c = lienzo.value;
  vista.zoom = Math.max(0.5, Math.min(2.5, Math.min(c.clientWidth / (ancho * LADO_ZONA), c.clientHeight / (alto * LADO_ZONA))));
}

const aPantalla = (zx, zy) => {
  const c = lienzo.value;
  const l = LADO_ZONA * vista.zoom;
  return [c.clientWidth / 2 + (zx - vista.x) * l, c.clientHeight / 2 + (zy - vista.y) * l];
};

let encuadrado = false;
function dibujar() {
  const c = lienzo.value;
  const d = datos.value;
  if (!c || !d) return;
  if (!encuadrado) { encuadrar(); encuadrado = true; }
  const ppp = window.devicePixelRatio || 1;
  c.width = c.clientWidth * ppp;
  c.height = c.clientHeight * ppp;
  const g = c.getContext("2d");
  g.setTransform(ppp, 0, 0, ppp, 0, 0);
  g.imageSmoothingEnabled = false;
  const l = LADO_ZONA * vista.zoom;
  // Fondo: todo el mundo con niebla; encima, las zonas descubiertas con su terreno.
  g.fillStyle = "#26362b";
  g.fillRect(0, 0, c.clientWidth, c.clientHeight);
  const [x0, y0] = aPantalla(0, 0);
  g.fillStyle = "#34473a";
  g.fillRect(x0, y0, d.lado * l, d.lado * l);
  const baldosa = l / 4;                  // cada zona se ve como 4 × 4 baldosas de hierba
  for (const z of d.zonas) {
    const [px, py] = aPantalla(z.x, z.y);
    const muestra = muestras[z.bioma];
    if (muestra) {
      for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) g.drawImage(muestra, px + i * baldosa, py + j * baldosa, baldosa + 0.5, baldosa + 0.5);
    } else {
      g.fillStyle = TERRENO[z.bioma] ?? TERRENO.pradera;
      g.fillRect(px, py, l + 0.5, l + 0.5);
    }
  }
  g.strokeStyle = "rgba(0,0,0,0.08)";
  for (const z of d.zonas) { const [px, py] = aPantalla(z.x, z.y); g.strokeRect(px + 0.5, py + 0.5, l - 1, l - 1); }
  // Caminos entre asentamientos.
  const porId = new Map(d.asentamientos.map((a) => [a.id, a]));
  g.strokeStyle = "#c79a58";
  g.lineWidth = Math.max(2, 3 * vista.zoom);
  g.setLineDash([6 * vista.zoom, 4 * vista.zoom]);
  for (const [a, b] of d.caminos) {
    const p = porId.get(a); const q = porId.get(b);
    if (!p || !q) continue;
    const [ax, ay] = aPantalla(p.zona[0] + 0.5, p.zona[1] + 0.5);
    const [bx, by] = aPantalla(q.zona[0] + 0.5, q.zona[1] + 0.5);
    g.beginPath(); g.moveTo(ax, ay); g.lineTo(bx, by); g.stroke();
  }
  g.setLineDash([]);
  // Relaciones entre pueblos, villas y ciudades: alianzas, tributos y rivalidades.
  const linea = (a, b, color, ancho, raya) => {
    const p = porId.get(a); const q = porId.get(b);
    if (!p || !q) return;
    const [ax, ay] = aPantalla(p.zona[0] + 0.5, p.zona[1] + 0.5);
    const [bx, by] = aPantalla(q.zona[0] + 0.5, q.zona[1] + 0.5);
    g.strokeStyle = color; g.lineWidth = ancho; g.setLineDash(raya);
    g.beginPath(); g.moveTo(ax, ay); g.lineTo(bx, by); g.stroke();
  };
  for (const [a, b] of d.alianzas ?? []) linea(a, b, RELACION.alianza, Math.max(2, 2.5 * vista.zoom), []);
  for (const [a, b] of d.vasallos ?? []) linea(a, b, RELACION.tributo, Math.max(2, 2 * vista.zoom), [2 * vista.zoom, 3 * vista.zoom]);
  for (const [a, b] of d.rivalidades ?? []) linea(a, b, RELACION.rivalidad, Math.max(1.5, 1.5 * vista.zoom), [5 * vista.zoom, 4 * vista.zoom]);
  g.setLineDash([]);
  // Asentamientos: icono, nombre y población.
  for (const a of d.asentamientos) {
    const [cx, cy] = aPantalla(a.zona[0] + 0.5, a.zona[1] + 0.5);
    const [sx, sy, sw, sh] = ICONO[a.tipo] ?? ICONO.aldea;
    const escala = (l * 0.7) / Math.max(sw, sh);
    if (casas.complete) g.drawImage(casas, sx, sy, sw, sh, cx - (sw * escala) / 2, cy - (sh * escala) / 2 - l * 0.08, sw * escala, sh * escala);
    if (a.id === ruta.aldea) {
      g.strokeStyle = "#f2cf5b"; g.lineWidth = 2;
      g.strokeRect(cx - l / 2 + 2, cy - l / 2 + 2, l - 4, l - 4);
    }
    if (vista.zoom >= 0.7) {
      // Nombre recortado al ancho de la zona y, debajo, la población.
      const t = Math.round(10 * Math.min(1.5, vista.zoom));
      g.font = `600 ${t}px Inter, sans-serif`;
      g.textAlign = "center";
      g.lineWidth = 3; g.strokeStyle = "rgba(20,30,20,0.85)"; g.fillStyle = "#fff";
      const nombre = recortar(g, a.nombre, l - 6);
      const poblacion = numero(a.poblacion);
      g.strokeText(nombre, cx, cy + l / 2 - t - 4); g.fillText(nombre, cx, cy + l / 2 - t - 4);
      g.font = `500 ${t}px Inter, sans-serif`;
      g.strokeText(poblacion, cx, cy + l / 2 - 3); g.fillText(poblacion, cx, cy + l / 2 - 3);
    }
  }
}

// Arrastrar, acercar y pulsar.
let arrastre = null;
function bajar(e) { arrastre = { x: e.clientX, y: e.clientY, movido: false }; lienzo.value.setPointerCapture(e.pointerId); }
function mover(e) {
  if (!arrastre) return;
  const dx = e.clientX - arrastre.x; const dy = e.clientY - arrastre.y;
  if (Math.abs(dx) + Math.abs(dy) > 3) arrastre.movido = true;
  vista.x -= dx / (LADO_ZONA * vista.zoom); vista.y -= dy / (LADO_ZONA * vista.zoom);
  arrastre.x = e.clientX; arrastre.y = e.clientY;
  dibujar();
}
function subir(e) {
  const pulsado = arrastre && !arrastre.movido;
  arrastre = null;
  if (!pulsado || !datos.value) return;
  const r = lienzo.value.getBoundingClientRect();
  const l = LADO_ZONA * vista.zoom;
  const zx = vista.x + (e.clientX - r.left - r.width / 2) / l;
  const zy = vista.y + (e.clientY - r.top - r.height / 2) / l;
  const a = datos.value.asentamientos.find((s) => Math.floor(zx) === s.zona[0] && Math.floor(zy) === s.zona[1]);
  if (a) cambiarAldea(a.id);
}
function rueda(e) {
  e.preventDefault();
  vista.zoom = Math.max(0.35, Math.min(3, vista.zoom * (e.deltaY < 0 ? 1.2 : 1 / 1.2)));
  dibujar();
}

let reloj;
let observador;
onMounted(() => {
  cargar();
  reloj = setInterval(cargar, 5000);
  observador = new ResizeObserver(() => dibujar());
  observador.observe(caja.value);
});
onBeforeUnmount(() => { clearInterval(reloj); observador?.disconnect(); });

const lista = computed(() => [...(datos.value?.asentamientos ?? [])].sort((a, b) => b.poblacion - a.poblacion));
const pestana = computed(() => (ruta.pestana === "historia" ? "historia" : "asentamientos"));
const opciones = computed(() => [
  { id: "asentamientos", texto: "Asentamientos", cuenta: lista.value.length },
  { id: "historia", texto: "Historia" },
]);
const PLURAL = { aldea: "aldeas", pueblo: "pueblos", villa: "villas", ciudad: "ciudades" };
// Un punto por año; en el globo, cuánta gente vive en cada tipo de asentamiento.
const anual = computed(() => (datos.value?.anual ?? []).map((f) => ({
  ano: f.ano,
  poblacion: f.poblacion,
  detalle: Object.entries(f.gente).filter(([t]) => f.asentamientos[t])
    .map(([t, n]) => `${numero(n)} en ${f.asentamientos[t]} ${f.asentamientos[t] > 1 ? PLURAL[t] : TEXTO_TIPO[t].toLowerCase()}`),
})));
// Cuánto creció el mundo en el último año acabado (la última foto es la del año en curso).
const crecimiento = computed(() => {
  const a = datos.value?.anual ?? [];
  if (a.length < 3) return null;
  const [antes, despues] = [a[a.length - 3], a[a.length - 2]];
  return antes.poblacion ? { ano: despues.ano, cambio: Math.round(((despues.poblacion - antes.poblacion) / antes.poblacion) * 100) } : null;
});
const cuentas = computed(() => {
  const c = { aldea: 0, pueblo: 0, villa: 0, ciudad: 0 };
  for (const a of lista.value) c[a.tipo] = (c[a.tipo] ?? 0) + 1;
  return c;
});
</script>

<template>
  <div class="mundo">
    <div ref="caja" class="lienzo-caja tarjeta">
      <div v-if="fase === 'cargando'" class="esqueleto" style="position: absolute; inset: 0"></div>
      <p v-else-if="fase === 'error'" class="vacia">No hemos podido cargar el mapa del mundo. Lo volvemos a intentar en unos segundos.</p>
      <canvas ref="lienzo" class="lienzo" aria-label="Mapa del mundo con sus asentamientos"
              @pointerdown="bajar" @pointermove="mover" @pointerup="subir" @wheel="rueda"></canvas>
      <p class="ayuda">Arrastra para moverte, usa la rueda para acercarte y pulsa un asentamiento para entrar.</p>
    </div>

    <aside v-if="datos" class="resumen">
      <div class="cifras">
        <Cifra etiqueta="Personas en el mundo" :valor="numero(datos.poblacion)" />
        <Cifra etiqueta="Asentamientos" :valor="lista.length" />
      </div>
      <p class="tipos numero">
        <template v-for="(n, tipo) in cuentas" :key="tipo"><span v-if="n">{{ n }} {{ TEXTO_TIPO[tipo].toLowerCase() }}{{ n > 1 ? (tipo === "ciudad" ? "es" : "s") : "" }}</span></template>
      </p>
      <ul class="leyenda" aria-label="Leyenda del mapa">
        <li><span class="raya camino"></span>Camino</li>
        <li><span class="raya" :style="{ background: RELACION.alianza }"></span>Alianza</li>
        <li><span class="raya punteada" :style="{ color: RELACION.tributo }"></span>Tributo</li>
        <li><span class="raya punteada" :style="{ color: RELACION.rivalidad }"></span>Rivalidad</li>
      </ul>
      <Subpestanas :opciones="opciones" :activa="pestana" etiqueta="Partes del resumen del mundo" @elegir="irPestana" />
      <ul v-if="pestana === 'asentamientos'" class="lista">
        <li v-for="a in lista" :key="a.id">
          <button type="button" :class="{ on: a.id === ruta.aldea }" @click="cambiarAldea(a.id)">
            <span class="nombre">{{ a.nombre }}</span>
            <span class="detalle numero">{{ TEXTO_TIPO[a.tipo] }} · {{ mayuscula(a.bioma) }} · {{ numero(a.poblacion) }}</span>
          </button>
        </li>
      </ul>
      <template v-else>
        <h3>Personas en el mundo, año a año</h3>
        <p v-if="crecimiento" class="tipos">En el año {{ crecimiento.ano }} {{ crecimiento.cambio >= 0 ? "creció" : "bajó" }} un {{ Math.abs(crecimiento.cambio) }} %.</p>
        <GraficaPoblacion v-if="anual.length" :resumenes="anual" :maximo="0" unidad="personas" />
        <p v-else class="vacia">La gráfica empieza a dibujarse al acabar el primer día del mundo.</p>
        <h3>Grandes momentos</h3>
        <p v-if="!datos.momentos?.length" class="vacia">Todavía no ha llegado ningún gran momento. El primero será la fundación de la segunda aldea.</p>
        <ol v-else class="momentos">
          <li v-for="(s, i) in [...datos.momentos].reverse()" :key="'m' + i"><span class="ano numero">Año {{ s.ano }}</span>{{ s.texto }}</li>
        </ol>
        <h3>Lo último</h3>
        <p v-if="!datos.sucesos.length" class="vacia">Todavía no ha pasado nada en el mundo.</p>
        <ol v-else class="momentos">
          <li v-for="(s, i) in [...datos.sucesos].reverse().slice(0, 20)" :key="'s' + i"><span class="ano numero">Año {{ s.ano }}</span>{{ s.texto }}</li>
        </ol>
      </template>
    </aside>
  </div>
</template>

<style scoped>
.mundo { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: var(--space-4); height: 100%; min-height: 0; }
.lienzo-caja { position: relative; padding: 0; overflow: hidden; min-height: 420px; }
.lienzo { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
.lienzo:active { cursor: grabbing; }
.ayuda {
  position: absolute; left: var(--space-3); bottom: var(--space-3); margin: 0; padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm); font-size: var(--text-xs); color: #fff; background: rgba(20, 30, 20, 0.6); pointer-events: none;
}
.resumen { display: flex; flex-direction: column; gap: var(--space-3); overflow-y: auto; min-height: 0; }
.resumen > * { flex: none; }
.cifras { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.tipos { margin: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted); }
h3 { margin-top: var(--space-2); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
.lista button {
  display: flex; flex-direction: column; align-items: flex-start; width: 100%; padding: var(--space-2);
  border: none; border-radius: var(--radius-md); background: transparent; color: inherit; font: inherit; text-align: left; cursor: pointer;
}
.lista button:hover { background: var(--color-surface-muted); }
.lista button.on { border-radius: 0; background: var(--active-line) top / 100% 1px no-repeat, var(--active-line) bottom / 100% 1px no-repeat, var(--active-glow); }
.nombre { font-weight: 600; font-size: var(--text-sm); }
.detalle { font-size: var(--text-xs); color: var(--color-text-muted); }
.momentos { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2); font-size: var(--text-sm); }
.momentos li { display: flex; flex-direction: column; }
.ano { font-size: var(--text-xs); color: var(--color-text-muted); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.leyenda { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-3); font-size: var(--text-xs); color: var(--color-text-muted); }
.leyenda li { display: inline-flex; align-items: center; gap: var(--space-1); }
.raya { display: inline-block; width: 18px; height: 3px; border-radius: 2px; }
.raya.camino { background: repeating-linear-gradient(90deg, #c79a58 0 6px, transparent 6px 9px); }
.raya.punteada { background: repeating-linear-gradient(90deg, currentColor 0 3px, transparent 3px 6px); }
@media (max-width: 960px) {
  .mundo { grid-template-columns: 1fr; height: auto; }
  .lienzo-caja { height: 60vh; }
}
</style>
