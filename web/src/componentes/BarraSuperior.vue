<script setup>
import { computed, ref } from "vue";
import Icono from "./Icono.vue";
import SelectorTema from "./SelectorTema.vue";
import SelectorAldea from "./SelectorAldea.vue";
import { mayuscula } from "../textos.js";
import { alternarSonido, sonido } from "../sonido.js";
import { ir } from "../ruta.js";

const props = defineProps({ aldea: Object, conectado: Boolean, pequeno: Boolean });
const emit = defineEmits(["menu"]);
const ajustes = ref(false);

const ICONOS = {
  comida: "/sprites/Items/Food/Onigiri.png",
  madera: "/sprites/Items/Resource/Branch.png",
  piedra: "/sprites/Items/Resource/Rock.png",
};

// «En directo», «En directo · ×10» si el mundo va acelerado o «En pausa» (desde el panel de administración).
const directo = computed(() => {
  if (!props.conectado) return "Reconectando";
  if (props.aldea?.pausado) return "En pausa";
  const velocidad = props.aldea ? Math.round(10 / props.aldea.segundos_por_turno) : 1;
  return velocidad > 1 ? `En directo · ×${velocidad}` : "En directo";
});
const fecha = computed(() => {
  const a = props.aldea;
  if (!a) return "";
  const minutos = Math.floor(a.hora * 60);
  const hora = `${String(Math.floor(minutos / 60)).padStart(2, "0")}:${String(minutos % 60).padStart(2, "0")}`;
  return { larga: `Año ${a.ano} · ${mayuscula(a.estacion)} · Día ${a.dia} · ${hora}`, corta: `${mayuscula(a.estacion)} · ${hora}` };
});
</script>

<template>
  <header class="barra">
    <div class="marca flotante">
      <SelectorAldea :nombre="aldea?.nombre" />
      <span class="directo" :class="{ cortado: !conectado || aldea?.pausado }">
        <span class="punto" aria-hidden="true"></span><span class="texto-directo">{{ directo }}</span>
      </span>
    </div>

    <div v-if="aldea" class="estado flotante">
      <span class="fecha numero"><span class="larga">{{ fecha.larga }}</span><span class="corta">{{ fecha.corta }}</span></span>
      <!-- Cuánta gente hay en todo el mundo: el objetivo del mundo es crecer. Lleva al mapa del mundo. -->
      <button v-if="aldea.mundo" type="button" class="mundo numero" title="Personas en todo el mundo. Pulsa para ver el mapa del mundo."
              :aria-label="`${aldea.mundo.poblacion} personas en el mundo, en ${aldea.mundo.asentamientos} asentamientos. Ver el mapa del mundo`"
              @click="ir('mundo')">
        <Icono nombre="globo" :tamano="16" />{{ aldea.mundo.poblacion.toLocaleString("es-ES") }}<span class="larga"> en el mundo</span>
      </button>
      <template v-if="!pequeno">
        <span class="separador" aria-hidden="true"></span>
        <span v-for="(valor, recurso) in aldea.recursos" :key="recurso" class="recurso numero" :title="mayuscula(recurso)">
          <img class="icono-pixel" :src="ICONOS[recurso]" :alt="mayuscula(recurso)" />{{ valor }}
        </span>
        <span class="recurso numero muralla" title="Tramos de muralla construidos">Muralla {{ aldea.muralla }}/20</span>
        <span class="separador" aria-hidden="true"></span>
        <button type="button" class="boton-icono" :class="{ on: sonido.activo }" :aria-pressed="sonido.activo"
                :aria-label="sonido.activo ? 'Apagar el sonido' : 'Encender el sonido'" :title="sonido.activo ? 'Apagar el sonido' : 'Encender el sonido'"
                @click="alternarSonido"><Icono :nombre="sonido.activo ? 'altavoz' : 'silencio'" /></button>
        <div class="ajustes">
          <button type="button" class="boton-icono" :class="{ on: ajustes }" aria-label="Ajustes" :aria-expanded="ajustes"
                  @click="ajustes = !ajustes"><Icono nombre="ajustes" /></button>
          <div v-if="ajustes" class="desplegable flotante">
            <p class="titulo">Colores</p>
            <SelectorTema />
          </div>
        </div>
      </template>
      <button v-else type="button" class="boton-icono" aria-label="Menú" @click="emit('menu')"><Icono nombre="menu" /></button>
    </div>
  </header>
</template>

<style scoped>
.barra {
  /* Por encima de la columna de iconos, para que los desplegables (aldeas, ajustes) no queden debajo. */
  position: absolute; top: var(--space-4); left: var(--space-4); right: var(--space-4); z-index: 22;
  display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-3);
  pointer-events: none;
}
.barra > * { pointer-events: auto; }
.marca, .estado { display: flex; align-items: center; gap: var(--space-3); height: 52px; padding: 0 var(--space-4); border-radius: var(--radius-lg); }
.estado { padding: 0 var(--space-1) 0 var(--space-4); }
.nombre { font-family: var(--font-pixel); font-size: var(--text-xl); font-weight: 600; letter-spacing: 0.02em; }
.directo { white-space: nowrap; display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--panel-texto-suave); }
.punto { width: 8px; height: 8px; border-radius: 50%; background: var(--en-directo); box-shadow: 0 0 0 3px color-mix(in srgb, var(--en-directo) 30%, transparent); }
.cortado .punto { background: var(--warning); box-shadow: none; }
.fecha { font-size: var(--text-sm); font-weight: 500; white-space: nowrap; }
.mundo {
  display: inline-flex; align-items: center; gap: var(--space-1); height: 32px; padding: 0 var(--space-2);
  border: 1px solid color-mix(in srgb, var(--color-accent) 45%, transparent); border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-accent) 12%, transparent); color: inherit;
  font: inherit; font-size: var(--text-sm); font-weight: 600; white-space: nowrap; cursor: pointer;
}
.mundo svg { color: var(--color-accent); }
.mundo:hover { background: color-mix(in srgb, var(--color-accent) 22%, transparent); }
.mundo:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
.separador { width: 1px; height: 24px; background: var(--panel-borde); }
.recurso { display: inline-flex; align-items: center; gap: var(--space-1); font-size: var(--text-sm); font-weight: 600; white-space: nowrap; }
.ajustes { position: relative; }
.desplegable { position: absolute; right: 0; top: calc(100% + var(--space-2)); padding: var(--space-3); min-width: 240px; }
.desplegable .titulo { margin: 0 0 var(--space-2); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--panel-texto-suave); }
.corta { display: none; }
@media (max-width: 1100px) { .muralla { display: none; } }
@media (max-width: 960px) { .larga { display: none; } .corta { display: inline; } }
@media (max-width: 760px) {
  .barra { top: var(--space-2); left: var(--space-2); right: var(--space-2); }
  .marca, .estado { height: 48px; }
  .marca { padding: 0 var(--space-3); }
  .texto-directo { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
}
</style>
