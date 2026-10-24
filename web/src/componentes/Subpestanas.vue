<script setup>
// Subpestañas dentro de una sección, con el recuento de cada una si lo tiene (no se enseña el cero).
// `opciones`: [{ id, texto, cuenta? }]. Emite el id elegido.
defineProps({ opciones: Array, activa: String, etiqueta: String });
const emit = defineEmits(["elegir"]);
</script>

<template>
  <div class="subpestanas" role="tablist" :aria-label="etiqueta">
    <button v-for="o in opciones" :key="o.id" type="button" role="tab" class="pestana" :class="{ on: activa === o.id }"
            :aria-selected="activa === o.id" @click="emit('elegir', o.id)">
      {{ o.texto }}<span v-if="o.cuenta" class="cuenta numero">{{ o.cuenta }}</span>
    </button>
  </div>
</template>

<style scoped>
.subpestanas {
  display: flex; overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid var(--color-border); margin: 0 calc(-1 * var(--space-2));
  padding: 0 var(--space-2);
}
.subpestanas::-webkit-scrollbar { display: none; }
.pestana {
  display: inline-flex; align-items: center; gap: 6px; flex: none;
  height: 40px; padding: 0 var(--space-2); border: none; background: transparent;
  color: var(--color-text-muted); font: inherit; font-size: var(--text-sm); font-weight: 500; cursor: pointer;
  transition: color var(--duration) var(--ease);
}
.pestana:hover { color: var(--color-text); }
.pestana.on { color: var(--color-text); font-weight: 600; background: var(--active-line) bottom / 100% 2px no-repeat; }
.pestana:focus-visible { outline: 2px solid var(--color-focus); outline-offset: -2px; border-radius: var(--radius-sm); }
.cuenta {
  min-width: 20px; padding: 0 5px; border-radius: var(--radius-sm); line-height: 20px; text-align: center;
  font-size: var(--text-xs); font-weight: 600; background: var(--color-surface-muted); color: var(--color-text-muted);
}
.pestana.on .cuenta { background: color-mix(in srgb, var(--color-accent) 18%, transparent); color: var(--color-text); }
</style>
