<script setup>
// Vida de un pueblo, villa o ciudad: oro e impuestos, descontento, especialidad del terreno,
// avances y lo que se investiga, monumentos, y aliados, rivales, señor y vasallos.
import { computed } from "vue";
import { cambiarAldea } from "../ruta.js";

const props = defineProps({ sociedad: Object, relaciones: Object });
const numero = (n) => n.toLocaleString("es-ES");
const s = computed(() => props.sociedad);
const r = computed(() => props.relaciones ?? {});
const nombres = (lista) => lista ?? [];
const mayus = (t) => t.charAt(0).toUpperCase() + t.slice(1);
const hayRelaciones = computed(() => r.value.senor || nombres(r.value.aliados).length || nombres(r.value.rivales).length
  || nombres(r.value.vasallos).length);
</script>

<template>
  <div class="sociedad">
    <div class="fila">
      <span class="dato"><span class="etiqueta">Oro</span><strong class="numero">{{ numero(s.oro) }}</strong></span>
      <span class="dato"><span class="etiqueta">Impuestos</span><strong>{{ mayus(s.impuesto) }}</strong></span>
      <span class="dato"><span class="etiqueta">Vende</span><strong>{{ s.especialidad }}</strong></span>
    </div>
    <div class="descontento">
      <span class="etiqueta">Descontento</span>
      <span class="pista" role="meter" aria-label="Descontento" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="Math.round(s.descontento * 100)">
        <span :class="{ alto: s.descontento >= 0.5 }" :style="{ width: s.descontento * 100 + '%' }"></span>
      </span>
      <span v-if="s.protesta" class="aviso">Protestas en la calle</span>
      <span v-else-if="s.hambruna" class="aviso">Sequía larga</span>
    </div>

    <p class="linea">
      <strong>Avances:</strong> {{ s.avances.length ? s.avances.join(", ") : "todavía ninguno" }}.
      <template v-if="s.investigando"> Ahora estudian {{ s.investigando.avance }}.</template>
    </p>
    <p v-if="s.monumentos.length || s.monumento" class="linea">
      <strong>Monumentos:</strong> {{ s.monumentos.join(", ") || "ninguno terminado" }}.
      <template v-if="s.monumento"> En obra: {{ s.monumento.nombre }} ({{ Math.round(100 * (1 - s.monumento.dias / s.monumento.total)) }} %).</template>
    </p>

    <div v-if="hayRelaciones" class="relaciones">
      <p v-if="r.senor" class="linea">Paga tributo a <button type="button" class="enlace" @click="cambiarAldea(r.senor.id)">{{ r.senor.nombre }}</button>.</p>
      <p v-if="nombres(r.vasallos).length" class="linea">Le pagan tributo:
        <template v-for="(v, i) in r.vasallos" :key="v.id"><button type="button" class="enlace" @click="cambiarAldea(v.id)">{{ v.nombre }}</button>{{ i < r.vasallos.length - 1 ? ", " : "." }}</template>
      </p>
      <p v-if="nombres(r.aliados).length" class="linea">Aliados:
        <template v-for="(v, i) in r.aliados" :key="v.id"><button type="button" class="enlace" @click="cambiarAldea(v.id)">{{ v.nombre }}</button>{{ i < r.aliados.length - 1 ? ", " : "." }}</template>
      </p>
      <p v-if="nombres(r.rivales).length" class="linea">Rivales:
        <template v-for="(v, i) in r.rivales" :key="v.id"><button type="button" class="enlace" @click="cambiarAldea(v.id)">{{ v.nombre }}</button>{{ i < r.rivales.length - 1 ? ", " : "." }}</template>
      </p>
    </div>
  </div>
</template>

<style scoped>
.sociedad { display: flex; flex-direction: column; gap: var(--space-2); }
.fila { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-2); }
.dato { display: flex; flex-direction: column; min-width: 0; padding: var(--space-2) var(--space-3); border-radius: var(--radius-md); background: var(--color-surface); border: 1px solid var(--color-border); }
.dato strong { font-size: var(--text-sm); overflow-wrap: anywhere; }
.etiqueta { font-size: var(--text-xs); color: var(--color-text-muted); }
.descontento { display: grid; grid-template-columns: auto minmax(60px, 1fr) auto; align-items: center; gap: var(--space-2); }
.pista { height: 6px; border-radius: 3px; background: var(--color-surface-muted); overflow: hidden; }
.pista span { display: block; height: 100%; border-radius: 3px; background: var(--warning); }
.pista span.alto { background: var(--danger); }
.aviso { font-size: var(--text-xs); padding-left: var(--space-2); border-left: 3px solid var(--warning); }
.linea { margin: 0; font-size: var(--text-sm); }
.relaciones { display: flex; flex-direction: column; gap: var(--space-1); }
.enlace { padding: 0; border: none; background: none; color: var(--color-primary); font: inherit; text-decoration: underline; text-underline-offset: 2px; cursor: pointer; }
.enlace:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; border-radius: 2px; }
</style>
