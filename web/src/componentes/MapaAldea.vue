<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import Icono from "./Icono.vue";
import { Escena } from "../mapa/escena.js";

const props = defineProps({ mapa: Object, aldea: Object, seleccionado: Number, siguiendo: Boolean, pequeno: Boolean,
  panelAbierto: Boolean });
const emit = defineEmits(["seleccionar", "dejarDeSeguir"]);
const lienzo = ref(null);
const listo = ref(false);
let escena;

onMounted(async () => {
  escena = new Escena(lienzo.value, {
    alSeleccionar: (id) => emit("seleccionar", id),
    alDejarDeSeguir: () => emit("dejarDeSeguir"),
  });
  await escena.iniciar(props.mapa);
  if (escena.destruido) return;          // se cambió de asentamiento mientras cargaba
  escena.mostrarMinimapa(!props.pequeno);
  if (props.aldea) await escena.actualizar(props.aldea);
  escena.marcar(props.seleccionado, props.siguiendo);
  listo.value = true;
});

watch(() => props.aldea, (aldea) => { if (listo.value && aldea) escena.actualizar(aldea); });
watch(() => [props.seleccionado, props.siguiendo], () => { if (listo.value) escena.marcar(props.seleccionado, props.siguiendo); });
watch(() => props.pequeno, (p) => { if (listo.value) escena.mostrarMinimapa(!p); });

onBeforeUnmount(() => escena?.destruir());
</script>

<template>
  <div ref="lienzo" class="lienzo" role="img" aria-label="Mapa de la aldea visto desde arriba, con sus habitantes moviéndose en directo"></div>
  <!-- En el móvil, con un panel abierto, el zoom se esconde: se transparentaba a través del panel. -->
  <div v-if="listo && !(pequeno && panelAbierto)" class="zoom flotante" :class="{ pequeno }">
    <button type="button" class="boton-icono" aria-label="Acercar" @click="escena.acercar()"><Icono nombre="mas" /></button>
    <button type="button" class="boton-icono" aria-label="Alejar" @click="escena.alejar()"><Icono nombre="menos" /></button>
    <button type="button" class="boton-icono" aria-label="Ver toda la aldea" title="Ver toda la aldea"
            @click="emit('dejarDeSeguir'); escena.verTodo()"><Icono nombre="todo" /></button>
  </div>
</template>

<style scoped>
.lienzo { position: absolute; inset: 0 0 var(--alto-estado) 0; cursor: grab; }
.lienzo:active { cursor: grabbing; }
/* Encima del minimapa, que mide 176 × 132 y está a 20 px de los bordes. */
.zoom {
  position: absolute; right: 20px; bottom: calc(172px + var(--alto-estado)); z-index: 10;
  display: flex; flex-direction: column; gap: 2px; padding: var(--space-1); border-radius: var(--radius-md);
}
.zoom.pequeno { right: var(--space-2); bottom: calc(168px + var(--alto-estado)); }
</style>
