<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <template v-for="(part, index) in parts" :key="index">
      <path
        v-if="part.tag === 'path'"
        :d="part.attrs.d"
        :fill="part.fill ? 'currentColor' : 'none'"
        :stroke="part.fill ? 'none' : 'currentColor'"
      />
      <circle
        v-else-if="part.tag === 'circle'"
        :cx="part.attrs.cx"
        :cy="part.attrs.cy"
        :r="part.attrs.r"
        :fill="part.fill ? 'currentColor' : 'none'"
        :stroke="part.fill ? 'none' : 'currentColor'"
      />
      <rect
        v-else-if="part.tag === 'rect'"
        :x="part.attrs.x"
        :y="part.attrs.y"
        :width="part.attrs.width"
        :height="part.attrs.height"
        :rx="part.attrs.rx"
        :fill="part.fill ? 'currentColor' : 'none'"
        :stroke="part.fill ? 'none' : 'currentColor'"
      />
    </template>
  </svg>
</template>

<script setup>
import { computed } from "vue";
import { iconPaths } from "./paths";

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  strokeWidth: { type: [Number, String], default: 2 },
  filled: { type: Boolean, default: false }
});

const parts = computed(() => {
  const paths = iconPaths[props.name];
  if (!paths) return [];
  const forceFill = props.filled || props.name === "star";
  return paths.map((part) => ({
    tag: part.tag,
    attrs: { ...part.attrs },
    fill: Boolean(part.fill || forceFill)
  }));
});
</script>

<style scoped>
.app-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
