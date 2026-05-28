<template>
  <div class="subject-picker">
    <template v-if="variant === 'filter'">
      <select :value="subjectId || ''" @change="onFilterChange">
        <option value="">Все предметы</option>
        <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
    </template>
    <template v-else>
      <div class="source-toggle">
        <button
          type="button"
          :class="['btn btn-sm', mode === 'catalog' ? 'btn-primary' : 'btn-secondary']"
          @click="setMode('catalog')"
        >
          Из справочника
        </button>
        <button
          type="button"
          :class="['btn btn-sm', mode === 'custom' ? 'btn-primary' : 'btn-secondary']"
          @click="setMode('custom')"
        >
          Свой предмет
        </button>
      </div>
      <select v-if="mode === 'catalog'" :value="subjectId || ''" @change="onCatalogChange">
        <option disabled value="">Выберите предмет</option>
        <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
      <input
        v-else
        :value="subjectCustom"
        maxlength="128"
        placeholder="Название предмета"
        @input="onCustomInput"
      />
    </template>
    <p v-if="loadError" class="text-danger picker-error">{{ loadError }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { api } from "../api/client";

const props = defineProps({
  variant: {
    type: String,
    default: "edit",
    validator: (v) => ["edit", "filter"].includes(v)
  },
  mode: { type: String, default: "catalog" },
  subjectId: { type: String, default: "" },
  subjectCustom: { type: String, default: "" }
});

const emit = defineEmits(["update:mode", "update:subjectId", "update:subjectCustom"]);

const subjects = ref([]);
const loadError = ref("");

async function loadSubjects() {
  loadError.value = "";
  try {
    subjects.value = await api.subjects();
  } catch (err) {
    loadError.value = err.message || "Не удалось загрузить предметы";
  }
}

function setMode(nextMode) {
  emit("update:mode", nextMode);
  if (nextMode === "catalog") {
    emit("update:subjectCustom", "");
  } else {
    emit("update:subjectId", "");
  }
}

function onCatalogChange(event) {
  emit("update:subjectId", event.target.value);
  emit("update:subjectCustom", "");
}

function onCustomInput(event) {
  emit("update:subjectCustom", event.target.value);
  emit("update:subjectId", "");
}

function onFilterChange(event) {
  emit("update:subjectId", event.target.value);
}

onMounted(loadSubjects);

watch(
  () => props.variant,
  () => {
    if (!subjects.value.length) loadSubjects();
  }
);
</script>

<style scoped>
.subject-picker {
  display: grid;
  gap: 6px;
  width: 100%;
}

.source-toggle {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.picker-error {
  margin: 0;
  font-size: 12px;
}
</style>
