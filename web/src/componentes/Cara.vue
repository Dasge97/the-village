<script setup>
// Cara de un personaje del paquete. Los que ya no viven en la aldea, en gris.
import { caraUrl } from "../textos.js";

defineProps({ personaje: String, nombre: String, vivo: { type: Boolean, default: true }, tamano: { type: Number, default: 38 } });
</script>

<template>
  <img class="cara" :class="{ ausente: !vivo }" :src="caraUrl(personaje)" :alt="`Cara de ${nombre}`"
       :width="tamano" :height="tamano" loading="lazy" />
</template>

<style scoped>
.cara {
  image-rendering: pixelated; flex: none;
  border-radius: var(--radius-sm); background: var(--color-surface-muted);
}
.ausente { filter: grayscale(1); opacity: 0.6; }
</style>
