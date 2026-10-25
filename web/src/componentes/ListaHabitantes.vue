<script setup>
// Quién vive en la aldea y qué hace ahora, con subpestañas por edad. Un punto junto a lo que
// hace dice si está despierto, durmiendo o fuera de la aldea.
import { computed } from "vue";
import Cara from "./Cara.vue";
import Cifra from "./Cifra.vue";
import SociedadGrande from "./SociedadGrande.vue";
import Subpestanas from "./Subpestanas.vue";
import { irPestana, ruta } from "../ruta.js";
import { accionEnTexto, mayuscula } from "../textos.js";

// `grande`: si es un pueblo, villa o ciudad, sus cifras (población por edades, consejo…). Allí la
// lista son sus notables, no toda la gente.
const props = defineProps({ habitantes: Array, seleccionado: Number, grande: Object, poblacion: Number, relaciones: Object });
const QUIEN = { jev: "Jev", reglas: "las reglas", presupuesto: "las reglas (Jev estaba ocupado)", respaldo: "las reglas" };
const numero = (n) => n.toLocaleString("es-ES");
const emit = defineEmits(["seleccionar"]);

const EDAD_ADULTA = 16;
const EDAD_MAYOR = 55;
const FILTROS = {
  todos: () => true,
  adultos: (h) => h.edad >= EDAD_ADULTA && h.edad < EDAD_MAYOR,
  ninos: (h) => h.edad < EDAD_ADULTA,
  mayores: (h) => h.edad >= EDAD_MAYOR,
};
const TEXTOS = { todos: "Todos", adultos: "Adultos", ninos: "Niños", mayores: "Mayores" };
const VACIA = {
  todos: "La aldea se ha quedado vacía. Si nadie llega pronto, vendrá un forastero.",
  adultos: "No queda ningún adulto en la aldea.",
  ninos: "Ahora mismo no hay niños en la aldea. El primero llegará cuando una pareja tenga un hijo.",
  mayores: "Nadie ha llegado todavía a los 55 años.",
};

const filtro = computed(() => (FILTROS[ruta.pestana] ? ruta.pestana : "todos"));
const opciones = computed(() => Object.keys(FILTROS).map((id) => ({ id, texto: TEXTOS[id], cuenta: props.habitantes.filter(FILTROS[id]).length })));

// Adultos primero, por edad; luego los niños.
const lista = computed(() => props.habitantes.filter(FILTROS[filtro.value])
  .sort((a, b) => (b.edad >= EDAD_ADULTA) - (a.edad >= EDAD_ADULTA) || b.edad - a.edad));

const estado = (h) => (h.fuera ? "fuera" : h.accion === "dormir" ? "durmiendo" : "despierto");
const oficio = (h) => (h.oficio ? mayuscula(h.oficio) : h.sexo === "m" ? "Niña" : "Niño");
</script>

<template>
  <div class="habitantes">
    <template v-if="grande">
      <p class="intro">Aquí viven demasiadas personas para seguirlas una a una. Estas son sus cifras y sus notables, la gente con cargo.</p>
      <div class="cifras-grande">
        <Cifra etiqueta="Viven aquí" :valor="numero(poblacion)" compacta />
        <Cifra etiqueta="Niños" :valor="numero(grande.edades.ninos)" compacta />
        <Cifra etiqueta="Adultos" :valor="numero(grande.edades.adultos)" compacta />
        <Cifra etiqueta="Mayores" :valor="numero(grande.edades.mayores)" compacta />
      </div>
      <p class="suave-grande numero">Casas para {{ numero(grande.capacidad) }} personas · tope de {{ numero(grande.tope) }}
        <template v-if="grande.obra"> · construyendo: {{ grande.obra }}</template></p>
      <p v-if="grande.consejo?.texto" class="consejo">
        <strong>El consejo decidió:</strong> {{ grande.consejo.texto }}
        <span class="suave-grande">({{ QUIEN[grande.consejo.quien] ?? "las reglas" }}<template v-if="grande.consejo.confianza != null">,
          {{ Math.round(grande.consejo.confianza * 100) }} %</template>)</span>
      </p>
      <SociedadGrande v-if="grande.sociedad" :sociedad="grande.sociedad" :relaciones="relaciones" />
      <h3 class="titulo-notables">Notables</h3>
    </template>
    <p v-else class="intro">Quién vive en la aldea y qué está haciendo ahora. Pulsa a alguien para ver su ficha.</p>
    <Subpestanas v-if="!grande" :opciones="opciones" :activa="filtro" etiqueta="Filtrar habitantes" @elegir="irPestana" />
    <p v-if="!lista.length" class="vacia">{{ VACIA[filtro] }}</p>
    <ul v-else class="lista">
      <li v-for="h in lista" :key="h.id">
        <button type="button" class="fila" :class="{ activo: seleccionado === h.id }" @click="emit('seleccionar', h.id)">
          <Cara :personaje="h.personaje" :nombre="h.nombre" :tamano="40" />
          <span class="texto">
            <span class="linea1"><span class="nombre">{{ h.nombre }}</span><span class="edad numero">{{ h.edad }} años</span></span>
            <span class="ahora"><span class="punto" :class="estado(h)" :title="mayuscula(estado(h))"></span>{{ accionEnTexto(h) }}</span>
          </span>
          <span class="oficio">{{ oficio(h) }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.habitantes { display: flex; flex-direction: column; gap: var(--space-3); }
.intro { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.cifras-grande { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2); }
.suave-grande { margin: 0; font-size: var(--text-xs); color: var(--color-text-muted); }
.consejo { margin: 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface); border: 1px solid var(--color-border); font-size: var(--text-sm); }
.titulo-notables { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.lista { list-style: none; margin: 0 calc(-1 * var(--space-2)); padding: 0; display: flex; flex-direction: column; gap: 2px; }
.fila {
  display: grid; grid-template-columns: 40px 1fr auto; align-items: center; gap: var(--space-3); width: 100%;
  padding: var(--space-2); border: none; border-radius: var(--radius-md); background: transparent;
  color: inherit; font: inherit; text-align: left; cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.fila:hover { background: var(--color-surface-muted); }
.fila:focus-visible { outline: 2px solid var(--color-focus); outline-offset: -2px; }
.fila.activo {
  border-radius: 0;
  background: var(--active-line) top / 100% 1px no-repeat, var(--active-line) bottom / 100% 1px no-repeat, var(--active-glow);
}
.texto { display: flex; flex-direction: column; min-width: 0; gap: 2px; }
.linea1 { display: flex; align-items: baseline; gap: var(--space-2); }
.nombre { font-weight: 600; }
.edad { font-size: var(--text-xs); color: var(--color-text-muted); }
.ahora { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.punto { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.punto.despierto { background: var(--success); }
.punto.durmiendo { background: var(--color-border-strong); }
.punto.fuera { background: var(--info); }
.oficio {
  padding: 2px var(--space-2); border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 500;
  background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-text-muted); white-space: nowrap;
}
.vacia { margin: var(--space-2) 0; font-size: var(--text-sm); color: var(--color-text-muted); }
</style>
