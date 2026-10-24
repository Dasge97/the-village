<script setup>
// Sucesos de la crónica en una línea de tiempo: lo más reciente arriba, un icono por tipo, la
// hora y cuánto hace. Con `porDias`, agrupados bajo el título de cada día del mundo.
import { computed } from "vue";
import Icono from "./Icono.vue";
import { diaDelTurno, grupoDeSuceso, haceCuanto, horaDelTurno, tituloDelDia } from "../textos.js";

const props = defineProps({ sucesos: Array, turno: Number, porDias: Boolean, compacta: Boolean });

const grupos = computed(() => {
  const salida = [];
  for (const s of props.sucesos) {
    const dia = diaDelTurno(s.turno);
    let g = salida[salida.length - 1];
    if (!g || (props.porDias && g.dia !== dia)) {
      g = { dia, titulo: tituloDelDia(s.turno), sucesos: [] };
      salida.push(g);
    }
    g.sucesos.push({ ...s, clave: `${s.turno}-${s.texto}`, grupo: grupoDeSuceso(s.tipo) });
  }
  return salida;
});
</script>

<template>
  <div class="sucesos" :class="{ compacta }">
    <section v-for="g in grupos" :key="g.dia" class="dia">
      <h3 v-if="porDias" class="titulo-dia">{{ g.titulo }}</h3>
      <ol>
        <li v-for="s in g.sucesos" :key="s.clave" class="suceso" :class="`grupo-${s.grupo.id}`">
          <span class="marca" aria-hidden="true"><Icono :nombre="s.grupo.icono" :tamano="compacta ? 14 : 16" /></span>
          <div class="contenido">
            <p class="texto">{{ s.texto }}</p>
            <p class="cuando numero">
              <time>{{ horaDelTurno(s.turno) }}</time><template v-if="turno != null"> · {{ haceCuanto(s.turno, turno) }}</template>
            </p>
          </div>
        </li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
.sucesos { display: flex; flex-direction: column; gap: var(--space-4); }
.titulo-dia {
  position: sticky; top: calc(-1 * var(--space-4)); z-index: 1; padding: var(--space-2) 0;
  font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--color-text-muted); background: var(--panel-bg);
}
ol { list-style: none; margin: 0; padding: 0; }
.suceso { position: relative; display: grid; grid-template-columns: 28px 1fr; gap: var(--space-3); padding-bottom: var(--space-3); }
/* Línea vertical que une los sucesos, por detrás de los iconos. */
.suceso:not(:last-child)::before {
  content: ""; position: absolute; left: 13px; top: 28px; bottom: 0; width: 2px;
  background: var(--color-border);
}
.marca {
  display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%;
  background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-text-muted);
}
.grupo-vida .marca { color: var(--color-accent); border-color: color-mix(in srgb, var(--color-accent) 45%, transparent); }
.contenido { min-width: 0; padding-top: 3px; }
.texto { margin: 0; font-size: var(--text-sm); line-height: 1.4; }
.grupo-vida .texto { font-weight: 500; }
.cuando { margin: 2px 0 0; font-size: var(--text-xs); color: var(--color-text-muted); }

.compacta .suceso { grid-template-columns: 24px 1fr; gap: var(--space-2); padding-bottom: var(--space-2); }
.compacta .suceso:not(:last-child)::before { left: 11px; top: 24px; }
.compacta .marca { width: 24px; height: 24px; }
.compacta .contenido { padding-top: 2px; }
</style>
