<script setup>
// La vida de una persona en una línea de tiempo: cómo llegó, sus momentos, sus hijos y cómo se fue.
// Cada momento lleva la fecha del mundo y la edad que tenía.
import Icono from "./Icono.vue";
import { fechaDelTurno, grupoDeSuceso, mayuscula } from "../textos.js";

defineProps({ vida: Array });

const ICONO = { llegada: "casa", nacimiento: "corazon", hijo: "corazon", salida: "chispa" };
const icono = (tipo) => ICONO[tipo] ?? grupoDeSuceso(tipo).icono;
const cuando = (m) => {
  const f = fechaDelTurno(Math.max(0, m.turno));
  return `${mayuscula(f.estacion)} del año ${f.ano} · ${m.edad} años`;
};
</script>

<template>
  <p v-if="!vida?.length" class="vacia">Todavía no le ha pasado nada que contar.</p>
  <ol v-else class="vida">
    <li v-for="(m, i) in vida" :key="i" :class="{ final: m.tipo === 'salida', destacado: ['nacimiento', 'hijo', 'pareja'].includes(m.tipo) }">
      <span class="marca" aria-hidden="true"><Icono :nombre="icono(m.tipo)" :tamano="14" /></span>
      <div>
        <p class="texto">{{ m.texto }}</p>
        <p class="cuando numero">{{ cuando(m) }}</p>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.vida { list-style: none; margin: 0; padding: 0; }
li { position: relative; display: grid; grid-template-columns: 24px 1fr; gap: var(--space-3); padding-bottom: var(--space-3); }
li:not(:last-child)::before { content: ""; position: absolute; left: 11px; top: 24px; bottom: 0; width: 2px; background: var(--color-border); }
.marca {
  display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%;
  background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-text-muted);
}
.destacado .marca { color: var(--color-accent); border-color: color-mix(in srgb, var(--color-accent) 45%, transparent); }
.final .marca { background: var(--color-surface-muted); }
p { margin: 0; }
.texto { font-size: var(--text-sm); line-height: 1.4; padding-top: 2px; }
.destacado .texto { font-weight: 500; }
.cuando { margin-top: 2px; font-size: var(--text-xs); color: var(--color-text-muted); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
</style>
