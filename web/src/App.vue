<script setup>
// Estilo "La ventana": el mapa ocupa toda la pantalla y la interfaz flota encima.
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { conectar } from "./conexion.js";
import { actualizarSonido, alternarSonido, sonido } from "./sonido.js";
import { climaDe } from "./mapa/efectos.js";
import { PANELES, alternarGrande, cambiarAldea, ir, ruta } from "./ruta.js";
import MapaAldea from "./componentes/MapaAldea.vue";
import BarraSuperior from "./componentes/BarraSuperior.vue";
import RielIconos from "./componentes/RielIconos.vue";
import BarraInferior from "./componentes/BarraInferior.vue";
import PanelFlotante from "./componentes/PanelFlotante.vue";
import TarjetaHabitante from "./componentes/TarjetaHabitante.vue";
import ListaHabitantes from "./componentes/ListaHabitantes.vue";
import FichaHabitante from "./componentes/FichaHabitante.vue";
import VistaInfo from "./componentes/VistaInfo.vue";
import VistaMundo from "./componentes/VistaMundo.vue";
import VistaNovedades from "./componentes/VistaNovedades.vue";
import VistaAdmin from "./componentes/VistaAdmin.vue";
import BarraEstado from "./componentes/BarraEstado.vue";
import ResumenDia from "./componentes/ResumenDia.vue";
import VistaFamilias from "./componentes/VistaFamilias.vue";
import VistaHistoria from "./componentes/VistaHistoria.vue";
import SelectorTema from "./componentes/SelectorTema.vue";
import Icono from "./componentes/Icono.vue";

const conexion = conectar();

// Pantalla pequeña: pestañas abajo en vez de la columna de iconos, y sin minimapa.
const consulta = window.matchMedia("(max-width: 760px)");
const pequeno = ref(consulta.matches);
const alCambiar = (e) => { pequeno.value = e.matches; };
onMounted(() => consulta.addEventListener("change", alCambiar));
onBeforeUnmount(() => consulta.removeEventListener("change", alCambiar));

// Habitante elegido: lo marca el mapa y lo enseña la tarjeta. Abrir su ficha también lo elige.
const elegido = ref(null);
const siguiendo = ref(false);
watch(() => [ruta.panel, ruta.id], ([panel, id]) => { if (panel === "habitantes" && id) elegido.value = id; }, { immediate: true });
watch(elegido, () => { siguiendo.value = false; });
watch(() => ruta.aldea, () => { elegido.value = null; });   // cada aldea tiene sus propios habitantes
watch(() => conexion.aldea?.habitantes, (lista) => {
  if (elegido.value && lista && !lista.some((h) => h.id === elegido.value)) elegido.value = null;
});

// Escape quita la selección del mapa cuando no hay ningún panel abierto.
const alPulsarTecla = (e) => { if (e.key === "Escape" && !ruta.panel) elegido.value = null; };
onMounted(() => window.addEventListener("keydown", alPulsarTecla));
onBeforeUnmount(() => window.removeEventListener("keydown", alPulsarTecla));

const menu = ref(false);

// Al entrar sin elegir asentamiento se ve el más poblado del mundo.
onMounted(async () => {
  if (location.hash.includes("aldea=")) return;
  try {
    const [primero] = await (await fetch("/api/aldeas")).json();
    if (primero?.existe && primero.id !== ruta.aldea && !ruta.panel) cambiarAldea(primero.id);
  } catch { /* se queda en La aldea */ }
});

// La música y los sonidos siguen al estado de la aldea (si están encendidos).
watch(() => conexion.aldea, (a) => { if (a) actualizarSonido(a, climaDe(a)); });
const nombreDe = (id) => conexion.aldea?.habitantes.find((h) => h.id === id)?.nombre;

const panel = computed(() => {
  const p = PANELES.find((x) => x.id === ruta.panel);
  if (!p) return null;
  const migas = [{ texto: "Mapa", ir: () => ir() }];
  let titulo = p.texto;
  if (p.id === "habitantes" && ruta.id) {
    migas.push({ texto: "Habitantes", ir: () => ir("habitantes") });
    titulo = nombreDe(ruta.id) ?? "Habitante";
  }
  // Historia se abre estrecha y se maximiza para ver además la historia año a año.
  const grande = p.id === "historia" && ruta.grande;
  return { ...p, titulo, migas, ancho: ["familias", "info", "mundo", "admin"].includes(p.id) || grande,
    maximizable: p.id === "historia", grande };
});
</script>

<template>
  <div class="ventana">
    <MapaAldea v-if="conexion.mapa" :mapa="conexion.mapa" :aldea="conexion.aldea" :seleccionado="elegido"
               :siguiendo="siguiendo" :pequeno="pequeno" :panel-abierto="!!panel"
               @seleccionar="(id) => (elegido = id)" @dejar-de-seguir="siguiendo = false" />
    <div v-else class="cargando esqueleto" aria-label="Cargando la aldea"></div>

    <BarraSuperior :aldea="conexion.aldea" :conectado="conexion.fase === 'conectado'" :pequeno="pequeno" @menu="menu = !menu" />
    <div v-if="menu && pequeno" class="menu flotante">
      <button type="button" class="opcion" @click="ir('mundo'); menu = false"><Icono nombre="mapa" />Mapa del mundo</button>
      <button type="button" class="opcion" @click="ir('info'); menu = false"><Icono nombre="info" />Qué es La aldea</button>
      <button type="button" class="opcion" :aria-pressed="sonido.activo" @click="alternarSonido">
        <Icono :nombre="sonido.activo ? 'altavoz' : 'silencio'" />{{ sonido.activo ? "Apagar el sonido" : "Encender el sonido" }}
      </button>
      <p class="titulo">Colores</p>
      <SelectorTema />
    </div>

    <RielIconos v-if="!pequeno" />
    <BarraInferior v-else />
    <BarraEstado :conectado="conexion.fase === 'conectado'" />

    <div v-if="conexion.fase === 'error'" class="aviso flotante" role="alert">
      <strong>No llegamos a la aldea</strong>
      <span>La conexión con el servidor se ha cortado. Seguimos intentándolo solos cada pocos segundos.</span>
    </div>

    <template v-if="conexion.aldea">
      <ResumenDia v-if="!panel" class="resumen-arriba" :sucesos="conexion.aldea.sucesos" :turno="conexion.aldea.turno"
                  @abrir="ir('historia')" />
      <div v-if="!panel" class="abajo">
        <TarjetaHabitante class="tarjeta-abajo" :habitantes="conexion.aldea.habitantes" :elegido="elegido"
                          @abrir="(id) => ir('habitantes', id)" @soltar="elegido = null" />
      </div>
      <PanelFlotante v-if="panel" :titulo="panel.titulo" :migas="panel.migas" :ancho="panel.ancho"
                     :maximizable="panel.maximizable" @cerrar="ir()" @maximizar="alternarGrande">
        <template v-if="panel.id === 'habitantes'">
          <FichaHabitante v-if="ruta.id" :id="ruta.id" :turno="conexion.aldea.turno" :siguiendo="siguiendo"
                          @seleccionar="(id) => ir('habitantes', id)" @cerrar="ir('habitantes')"
                          @seguir="siguiendo = !siguiendo" />
          <ListaHabitantes v-else :habitantes="conexion.aldea.habitantes" :seleccionado="elegido" :grande="conexion.aldea.grande"
                           :poblacion="conexion.aldea.poblacion"
                           @seleccionar="(id) => ir('habitantes', id)" />
        </template>
        <VistaFamilias v-else-if="panel.id === 'familias'" :turno="conexion.aldea.turno" />
        <VistaInfo v-else-if="panel.id === 'info'" :aldea="conexion.aldea" />
        <VistaMundo v-else-if="panel.id === 'mundo'" />
        <VistaNovedades v-else-if="panel.id === 'novedades'" />
        <VistaAdmin v-else-if="panel.id === 'admin'" />
        <VistaHistoria v-else :aldea="conexion.aldea" :grande="panel.grande" />
      </PanelFlotante>
    </template>
  </div>
</template>

<style scoped>
.ventana { position: fixed; inset: 0; overflow: hidden; background: oklch(0.62 0.1 125); }
.cargando { position: absolute; inset: 0; border-radius: 0; }

.abajo {
  position: absolute; left: var(--space-4); right: 220px; bottom: calc(var(--space-4) + var(--alto-estado)); z-index: 10;
  display: flex; align-items: flex-end; gap: var(--space-4); pointer-events: none;
}
.abajo > * { pointer-events: auto; }
.tarjeta-abajo { width: 320px; flex: none; }

/* Resumen del día: centrado bajo la barra de arriba. */
.resumen-arriba { position: absolute; z-index: 10; top: 84px; left: 50%; transform: translateX(-50%); width: max-content; max-width: min(560px, calc(100% - 220px)); }

.aviso {
  position: absolute; z-index: 30; top: 84px; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; gap: var(--space-1); max-width: 420px;
  padding: var(--space-3) var(--space-4); border-left: 3px solid var(--danger); font-size: var(--text-sm);
}

.menu {
  position: absolute; z-index: 30; top: 64px; right: var(--space-2); width: min(320px, calc(100% - 16px));
  padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);
}
.menu .opcion {
  display: flex; align-items: center; gap: var(--space-3); height: 44px; padding: 0 var(--space-2);
  border: none; border-radius: var(--radius-md); background: transparent; color: inherit; font: inherit; cursor: pointer;
}
.menu .opcion:hover { background: color-mix(in srgb, currentColor 10%, transparent); }
.menu .titulo { margin: var(--space-2) 0 0; font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--panel-texto-suave); }

@media (max-width: 760px) {
  .resumen-arriba { top: 64px; width: calc(100% - 16px); }
  .abajo { left: var(--space-2); right: var(--space-2); bottom: calc(76px + var(--alto-estado)); }
  .tarjeta-abajo { width: 100%; }
}
</style>
