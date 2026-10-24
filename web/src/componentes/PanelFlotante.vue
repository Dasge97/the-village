<script setup>
// Marco de cada sección: flota sobre el mapa, con migas de pan, título y botón de cerrar.
// `ancho` ocupa casi toda la pantalla (familias e historia maximizada); si no, es una columna
// estrecha. Con `maximizable` lleva un botón para pasar de estrecho a ancho y al revés.
import Icono from "./Icono.vue";

defineProps({ titulo: String, migas: { type: Array, default: () => [] }, ancho: Boolean, maximizable: Boolean });
const emit = defineEmits(["cerrar", "maximizar"]);
</script>

<template>
  <section class="panel flotante" :class="{ ancho }" role="dialog" :aria-label="titulo">
    <header class="cabecera">
      <div class="titulos">
        <nav v-if="migas.length" class="migas" aria-label="Estás en">
          <template v-for="(m, i) in migas" :key="i">
            <button type="button" @click="m.ir()">{{ m.texto }}</button><span aria-hidden="true">›</span>
          </template>
        </nav>
        <h2>{{ titulo }}</h2>
      </div>
      <div class="acciones">
        <button v-if="maximizable" type="button" class="boton-icono" :title="ancho ? 'Reducir' : 'Maximizar'"
                :aria-label="ancho ? 'Reducir el panel' : 'Maximizar el panel'" @click="emit('maximizar')">
          <Icono :nombre="ancho ? 'minimizar' : 'maximizar'" />
        </button>
        <button type="button" class="boton-icono" aria-label="Cerrar y volver al mapa" @click="emit('cerrar')">
          <Icono nombre="cerrar" />
        </button>
      </div>
    </header>
    <div class="cuerpo"><slot /></div>
  </section>
</template>

<style scoped>
.panel {
  position: absolute; z-index: 15; top: 84px; bottom: calc(var(--space-4) + var(--alto-estado)); left: 96px; width: 420px;
  display: flex; flex-direction: column; overflow: hidden;
  animation: entrar var(--duration) var(--ease);
}
.panel.ancho { right: var(--space-4); width: auto; }
@keyframes entrar { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: none; } }
.cabecera {
  display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3);
  padding: var(--space-4) var(--space-3) var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--panel-borde);
}
.titulos { min-width: 0; padding-top: var(--space-1); }
.acciones { display: flex; gap: var(--space-1); flex: none; }
h2 { font-family: var(--font-pixel); font-size: var(--text-xl); font-weight: 600; line-height: 1.2; }
.migas { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-1); font-size: var(--text-xs); color: var(--panel-texto-suave); margin-bottom: 2px; }
.migas button { border: none; background: none; padding: 0; color: inherit; font: inherit; cursor: pointer; }
.migas button:hover { color: var(--panel-texto); text-decoration: underline; }
.cuerpo { flex: 1; min-height: 0; overflow-y: auto; padding: var(--space-4) var(--space-6) var(--space-6); display: flex; flex-direction: column; gap: var(--space-4); }
@media (max-width: 760px) {
  .panel, .panel.ancho { top: 64px; left: var(--space-2); right: var(--space-2); bottom: calc(76px + var(--alto-estado)); width: auto; }
  .cabecera { padding-left: var(--space-4); }
  .cuerpo { padding: var(--space-3) var(--space-4) var(--space-4); }
}
@media (prefers-reduced-motion: reduce) { .panel { animation: none; } }
</style>
