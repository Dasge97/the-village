<script setup>
// Resumen del día, bajo la barra de arriba: lo más importante de las últimas 24 horas del mundo
// (una hora real), para quien entra por primera vez. Se puede cerrar hasta el día siguiente.
import { computed, ref } from "vue";
import Icono from "./Icono.vue";
import { SUCESOS_RUTINA, diaDelTurno, grupoDeSuceso } from "../textos.js";

const props = defineProps({ sucesos: Array, turno: Number });
const emit = defineEmits(["abrir"]);
const TURNOS_DIA = 360;

const CUENTAS = [
  { tipos: ["nacimiento"], uno: "nacimiento", varios: "nacimientos" },
  { tipos: ["muerte"], uno: "muerte", varios: "muertes" },
  { tipos: ["pareja"], uno: "pareja nueva", varios: "parejas nuevas" },
  { tipos: ["ataque"], uno: "ataque", varios: "ataques" },
  { tipos: ["casa", "muralla"], uno: "obra terminada", varios: "obras terminadas" },
  { tipos: ["forastero"], uno: "forastero", varios: "forasteros" },
];
// Qué suceso se cuenta en la frase: primero la vida, luego los peligros, las obras y lo demás.
const ORDEN = ["vida", "peligros", "obras", "fuera", "otros"];

const hoy = computed(() => props.sucesos.filter((s) => s.turno > props.turno - TURNOS_DIA && !SUCESOS_RUTINA.has(s.tipo)));
const cuentas = computed(() => CUENTAS.map((c) => {
  const n = hoy.value.filter((s) => c.tipos.includes(s.tipo)).length;
  return n ? `${n} ${n === 1 ? c.uno : c.varios}` : null;
}).filter(Boolean));
const destacado = computed(() => [...hoy.value].reverse()
  .sort((a, b) => ORDEN.indexOf(grupoDeSuceso(a.tipo).id) - ORDEN.indexOf(grupoDeSuceso(b.tipo).id))[0] ?? null);

const leer = () => { try { return Number(localStorage.getItem("resumen-cerrado")); } catch { return NaN; } };
const cerradoEl = ref(leer());
const visible = computed(() => cerradoEl.value !== diaDelTurno(props.turno));
function cerrar() {
  cerradoEl.value = diaDelTurno(props.turno);
  try { localStorage.setItem("resumen-cerrado", String(cerradoEl.value)); } catch { /* sin almacenamiento */ }
}
</script>

<template>
  <div v-if="visible" class="resumen flotante" role="status">
    <button type="button" class="contenido" @click="emit('abrir')">
      <span class="titulo"><Icono nombre="sol" :tamano="14" />Hoy en la aldea</span>
      <span v-if="destacado" class="frase">{{ destacado.texto }}</span>
      <span v-else class="frase">Un día tranquilo: cada uno a lo suyo.</span>
      <span v-if="cuentas.length" class="cuentas numero">{{ cuentas.join(" · ") }}</span>
    </button>
    <button type="button" class="boton-icono cerrar" aria-label="Cerrar el resumen de hoy" @click="cerrar">
      <Icono nombre="cerrar" :tamano="14" />
    </button>
  </div>
</template>

<style scoped>
.resumen { display: flex; align-items: center; gap: var(--space-1); padding: var(--space-1) var(--space-1) var(--space-1) var(--space-3); }
.contenido {
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-width: 0; padding: var(--space-1) 0;
  border: none; background: none; color: inherit; font: inherit; text-align: left; cursor: pointer;
}
.titulo { display: inline-flex; align-items: center; gap: var(--space-1); font-size: var(--text-xs); font-weight: 600; color: var(--color-accent); }
.frase { font-size: var(--text-sm); max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cuentas { font-size: var(--text-xs); color: var(--color-text-muted); }
.cerrar { width: 32px; height: 32px; flex: none; }
.contenido:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; border-radius: var(--radius-sm); }
</style>
