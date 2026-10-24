<script setup>
// Sección Historia (antes Historia y Crónica por separado): cómo está la aldea hoy y todo lo que ha
// pasado en el último año del mundo, filtrado por tipo y agrupado por días. En grande añade, a la
// derecha, la historia año a año.
import { computed } from "vue";
import AnoAAno from "./AnoAAno.vue";
import Cifra from "./Cifra.vue";
import Icono from "./Icono.vue";
import ListaSucesos from "./ListaSucesos.vue";
import Subpestanas from "./Subpestanas.vue";
import { alternarGrande, irPestana, ruta } from "../ruta.js";
import { GRUPOS_SUCESO, SUCESOS_RUTINA, grupoDeSuceso, mayuscula } from "../textos.js";

const props = defineProps({ aldea: Object, grande: Boolean });
const TRAMOS = 20;

const ICONOS = {
  comida: "/sprites/Items/Food/Onigiri.png",
  madera: "/sprites/Items/Resource/Branch.png",
  piedra: "/sprites/Items/Resource/Rock.png",
};

const todos = computed(() => props.aldea.sucesos.filter((s) => !SUCESOS_RUTINA.has(s.tipo)).reverse());
const filtro = computed(() => (GRUPOS_SUCESO.some((g) => g.id === ruta.pestana) ? ruta.pestana : "todo"));
const opciones = computed(() => [
  { id: "todo", texto: "Todo", cuenta: todos.value.length },
  ...GRUPOS_SUCESO.map((g) => ({ id: g.id, texto: g.texto, cuenta: todos.value.filter((s) => grupoDeSuceso(s.tipo).id === g.id).length })),
]);
const lista = computed(() => (filtro.value === "todo" ? todos.value : todos.value.filter((s) => grupoDeSuceso(s.tipo).id === filtro.value)));
const VACIA = {
  todo: "Todavía no ha pasado nada importante. En cuanto alguien haga algo, aparecerá aquí.",
  vida: "Este año todavía no ha nacido, muerto ni se ha emparejado nadie.",
  obras: "Este año todavía no se ha construido nada ni ha cambiado nadie de oficio.",
  peligros: "Ningún peligro por ahora: ni ataques, ni incendios, ni robos.",
  fuera: "Nadie ha salido a explorar más allá del bosque este año.",
};
</script>

<template>
  <div class="historia" :class="{ grande }">
    <div class="principal">
      <p class="intro">Cómo está la aldea ahora y todo lo que ha pasado en el último año del mundo.</p>

      <section class="hoy" aria-label="La aldea hoy">
        <Cifra etiqueta="Habitantes" :valor="aldea.poblacion" compacta />
        <Cifra v-for="(valor, recurso) in aldea.recursos" :key="recurso" :etiqueta="mayuscula(recurso)" :valor="valor" :icono="ICONOS[recurso]" compacta />
        <Cifra class="muralla" etiqueta="Muralla" :valor="`${aldea.muralla} de ${TRAMOS} tramos`" compacta>
          <div class="barra" role="meter" aria-label="Muralla construida" aria-valuemin="0" :aria-valuemax="TRAMOS" :aria-valuenow="aldea.muralla">
            <div :style="{ width: (aldea.muralla / TRAMOS) * 100 + '%' }"></div>
          </div>
        </Cifra>
      </section>

      <button v-if="!grande" type="button" class="boton" @click="alternarGrande">
        <Icono nombre="maximizar" :tamano="18" />Ver en grande, con la historia año a año
      </button>

      <section class="sucesos" aria-label="Lo que ha pasado">
        <h3>Lo que ha pasado</h3>
        <Subpestanas :opciones="opciones" :activa="filtro" etiqueta="Filtrar sucesos" @elegir="(id) => irPestana(id === 'todo' ? null : id)" />
        <p v-if="!lista.length" class="vacia">{{ VACIA[filtro] }}</p>
        <ListaSucesos v-else :sucesos="lista" :turno="aldea.turno" por-dias />
      </section>
    </div>

    <AnoAAno v-if="grande" class="anual" :ano="aldea.ano" />
  </div>
</template>

<style scoped>
.historia { display: flex; flex-direction: column; gap: var(--space-6); }
.principal { display: flex; flex-direction: column; gap: var(--space-6); min-width: 0; }
.grande { display: grid; grid-template-columns: 420px minmax(0, 1fr); align-items: start; }
.intro { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.hoy { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-2); }
@media (max-width: 400px) { .hoy { grid-template-columns: 1fr 1fr; } }
.muralla { grid-column: 1 / -1; }
.barra { height: 8px; margin-top: var(--space-1); border-radius: 4px; background: var(--color-surface-muted); overflow: hidden; }
.barra > div { height: 100%; border-radius: 4px; background: var(--color-accent); transition: width var(--duration) var(--ease); }
.sucesos { display: flex; flex-direction: column; gap: var(--space-3); }
h3 { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.boton {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  height: var(--control-height); border-radius: var(--radius-md);
  border: 1px solid var(--color-border-strong); background: var(--color-surface); color: var(--color-text);
  font: inherit; font-size: var(--text-sm); font-weight: 500; cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.boton:hover { background: var(--color-surface-muted); }
.boton:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
/* En grande, la columna de año a año se queda a la vista mientras se recorren los sucesos. */
.grande .anual { position: sticky; top: 0; }
@media (max-width: 960px) {
  .grande { grid-template-columns: 1fr; }
  .grande .anual { position: static; }
}
</style>
