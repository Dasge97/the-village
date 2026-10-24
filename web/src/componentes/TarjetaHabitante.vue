<script setup>
// Tarjeta de abajo a la izquierda: el habitante elegido en el mapa. Al pulsarla se abre su ficha
// y con la X se deja de mirarlo. Sin nadie elegido no se enseña.
import { computed } from "vue";
import Cara from "./Cara.vue";
import Icono from "./Icono.vue";
import { accionEnTexto, mayuscula } from "../textos.js";

const props = defineProps({ habitantes: Array, elegido: Number });
const emit = defineEmits(["abrir", "soltar"]);

const h = computed(() => props.habitantes.find((x) => x.id === props.elegido) ?? null);
</script>

<template>
  <div v-if="h" class="tarjeta-h flotante">
    <button type="button" class="abrir" :aria-label="`Ver la ficha de ${h.nombre}`" @click="emit('abrir', h.id)">
      <Cara :personaje="h.personaje" :nombre="h.nombre" :tamano="48" />
      <span class="texto">
        <span class="linea1"><strong>{{ h.nombre }}</strong><span class="suave">{{ h.edad }} años</span></span>
        <span class="suave">{{ h.oficio ? mayuscula(h.oficio) : (h.sexo === "m" ? "Niña" : "Niño") }}</span>
        <span class="ahora">{{ accionEnTexto(h) }}</span>
      </span>
    </button>
    <button type="button" class="boton-icono soltar" aria-label="Dejar de mirar a este habitante" @click="emit('soltar')">
      <Icono nombre="cerrar" :tamano="16" />
    </button>
  </div>
</template>

<style scoped>
.tarjeta-h { position: relative; display: flex; align-items: center; padding: var(--space-3); padding-right: var(--space-8); }
.abrir {
  display: flex; align-items: center; gap: var(--space-3); min-width: 0; width: 100%;
  padding: 0; border: none; background: none; color: inherit; font: inherit; text-align: left; cursor: pointer;
}
.texto { display: flex; flex-direction: column; min-width: 0; line-height: 1.35; }
.linea1 { display: flex; align-items: baseline; gap: var(--space-2); font-size: var(--text-md); }
.suave { color: var(--panel-texto-suave); font-size: var(--text-sm); }
.ahora { font-size: var(--text-sm); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.soltar { position: absolute; top: var(--space-1); right: var(--space-1); width: 32px; height: 32px; }
</style>
