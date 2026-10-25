<script setup>
// Cómo va la aldea: en qué etapa está, qué edificios tiene y en qué estado, qué le falta por
// construir, las mejoras de la última etapa y lo último que decidió su consejo.
import { computed } from "vue";

const props = defineProps({ evolucion: Object, muralla: Number });
const QUIEN = { jev: "Jev", reglas: "las reglas", presupuesto: "las reglas (Jev estaba ocupado)", respaldo: "las reglas" };
const mayus = (t) => t.charAt(0).toUpperCase() + t.slice(1);
const estadoTexto = (e) => (e <= 0 ? "en ruinas" : e < 50 ? "estropeado" : null);
const e = computed(() => props.evolucion);
</script>

<template>
  <section class="evolucion" aria-label="Evolución de la aldea">
    <div class="cabecera">
      <h3>Etapa {{ e.etapa }} de {{ e.etapas }} · {{ e.nombre }}</h3>
      <span v-if="e.invierno_duro" class="aviso">Invierno duro</span>
    </div>
    <div class="pasos" role="meter" aria-label="Etapa de la aldea" aria-valuemin="1" :aria-valuemax="e.etapas" :aria-valuenow="e.etapa">
      <span v-for="k in e.etapas" :key="k" :class="{ hecho: k <= e.etapa }"></span>
    </div>
    <p v-if="e.obra" class="linea">Ahora construyen: <strong>{{ e.obra }}</strong>.</p>
    <p v-if="e.etapa === 1" class="linea suave">Cuando la muralla esté completa ({{ muralla }} de 20 tramos), podrán empezar los primeros edificios.</p>

    <ul v-if="e.edificios.length" class="edificios">
      <li v-for="b in e.edificios" :key="b.id" :title="mayus(b.efecto)">
        <span class="nombre">{{ mayus(b.nombre) }}</span>
        <span class="pista" :aria-label="`Estado ${b.estado} de 100`"><span :class="{ mal: b.estado < 50 }" :style="{ width: b.estado + '%' }"></span></span>
        <span v-if="estadoTexto(b.estado)" class="mal-texto">{{ estadoTexto(b.estado) }}</span>
      </li>
    </ul>
    <p v-if="e.pendientes.length" class="linea suave">
      Por construir: {{ e.pendientes.map((p) => p.nombre).join(", ") }}.
      <template v-if="e.plan"> El consejo quiere empezar por {{ e.plan }}.</template>
    </p>
    <p v-if="e.etapa >= 4" class="linea numero">
      Mejoras: {{ e.reforzados }} de 20 tramos reforzados · {{ e.casas_piedra }} casas de piedra · {{ e.faroles.length }} de 4 faroles.
    </p>
    <p v-if="e.consejo" class="consejo">
      <strong>El consejo decidió:</strong> {{ e.consejo.texto }}
      <span class="suave">({{ QUIEN[e.consejo.quien] ?? "las reglas" }}<template v-if="e.consejo.confianza != null">, {{ Math.round(e.consejo.confianza * 100) }} %</template>)</span>
    </p>
  </section>
</template>

<style scoped>
.evolucion { display: flex; flex-direction: column; gap: var(--space-2); }
.cabecera { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
h3 { margin: 0; font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.aviso { font-size: var(--text-xs); padding-left: var(--space-2); border-left: 3px solid var(--info); }
.pasos { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.pasos span { height: 6px; border-radius: 3px; background: var(--color-surface-muted); }
.pasos span.hecho { background: var(--color-accent); }
.linea { margin: 0; font-size: var(--text-sm); }
.suave { color: var(--color-text-muted); }
.edificios { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.edificios li { display: grid; grid-template-columns: minmax(0, 1fr) 80px auto; align-items: center; gap: var(--space-2); font-size: var(--text-sm); }
.nombre { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pista { height: 6px; border-radius: 3px; background: var(--color-surface-muted); overflow: hidden; }
.pista span { display: block; height: 100%; border-radius: 3px; background: var(--success); }
.pista span.mal { background: var(--warning); }
.mal-texto { font-size: var(--text-xs); color: var(--color-text-muted); }
.consejo { margin: 0; padding: var(--space-2) var(--space-3); border-radius: var(--radius-md); background: var(--color-surface); border: 1px solid var(--color-border); font-size: var(--text-sm); }
</style>
