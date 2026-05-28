<template>
  <section class="wizard animate-fade-up">
    <header class="wizard-head">
      <h1>Новый конспект</h1>
      <p>Заполните 3 шага для создания конспекта</p>
    </header>

    <div class="stepper">
      <div v-for="s in steps" :key="s.num" :class="['stepper-item', { active: step === s.num, done: step > s.num }]">
        <span class="stepper-dot">
          <AppIcon v-if="step > s.num" name="check" :size="14" />
          <span v-else>{{ s.num }}</span>
        </span>
        <span class="stepper-label">{{ s.label }}</span>
      </div>
      <div class="stepper-line" :style="{ width: `${((step - 1) / 2) * 100}%` }"></div>
    </div>

    <form class="wizard-body card" @submit.prevent="submit">
      <transition name="step" mode="out-in">
        <div v-if="step === 1" key="s1" class="step-content">
          <div class="field">
            <label for="wTitle">Название конспекта</label>
            <input id="wTitle" v-model.trim="form.title" maxlength="255" placeholder="Например: Органическая химия — лекция 5" />
          </div>
          <div class="field">
            <label for="wDesc">Краткое описание</label>
            <textarea id="wDesc" v-model.trim="form.description" maxlength="500" placeholder="О чём этот конспект?" rows="3" />
          </div>
          <div class="field">
            <div class="field-row">
              <label>Оглавление</label>
              <button class="btn btn-ghost btn-sm" type="button" @click="addOutline">
              <AppIcon name="plus" :size="14" /> Пункт
            </button>
            </div>
            <div class="outline-list">
              <div v-for="(item, i) in form.outline" :key="i" class="outline-row">
                <input v-model.trim="item.title" :placeholder="`Пункт ${i + 1}`" />
                <button type="button" class="btn btn-ghost btn-sm" aria-label="Удалить пункт" @click="removeOutline(i)">
                  <AppIcon name="close" :size="14" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="step === 2" key="s2" class="step-content">
          <div class="field">
            <label>Видимость</label>
            <div class="vis-grid">
              <button
                v-for="v in visOptions"
                :key="v.value"
                type="button"
                :class="['vis-card', { active: form.visibility === v.value }]"
                @click="form.visibility = v.value"
              >
                <AppIcon :name="v.icon" :size="22" class="vis-icon" />
                <span class="vis-title">{{ v.title }}</span>
                <span class="vis-desc">{{ v.desc }}</span>
              </button>
            </div>
          </div>

          <div v-if="form.visibility === 'group'" class="field animate-fade-in">
            <label>Группа</label>
            <select v-model="form.group_id">
              <option disabled value="">Выберите группу</option>
              <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
            </select>
          </div>

          <div class="field">
            <label>Предмет</label>
            <SubjectPicker
              v-model:mode="subjectMode"
              v-model:subject-id="form.subject_id"
              v-model:subject-custom="form.subject_custom"
            />
          </div>

          <div class="field">
            <label>Теги</label>
            <input v-model="tagsInput" placeholder="реакции, формулы, экзамен" />
          </div>
        </div>

        <div v-else key="s3" class="step-content">
          <h3 class="preview-title">Проверьте перед созданием</h3>
          <div class="preview-grid">
            <div class="preview-item">
              <span class="preview-label">Название</span>
              <span>{{ form.title }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Описание</span>
              <span>{{ form.description }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Видимость</span>
              <span class="badge badge-brand">{{ visibilityTitle }}</span>
            </div>
            <div class="preview-item" v-if="form.visibility === 'group'">
              <span class="preview-label">Группа</span>
              <span>{{ selectedGroupName || 'Не выбрана' }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Предмет</span>
              <span>{{ selectedSubjectName || form.subject_custom || 'Не указан' }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Теги</span>
              <span>{{ previewTags.length ? previewTags.join(', ') : 'Нет тегов' }}</span>
            </div>
            <div class="preview-item" v-if="previewOutline.length">
              <span class="preview-label">Оглавление</span>
              <ol class="preview-ol">
                <li v-for="item in previewOutline" :key="item.order">{{ item.title }}</li>
              </ol>
            </div>
          </div>
        </div>
      </transition>

      <p v-if="stepError" class="text-danger animate-fade-in">{{ stepError }}</p>
      <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>

      <div class="actions">
        <button v-if="step > 1" class="btn btn-secondary" type="button" @click="step--">
          <AppIcon name="arrow-left" :size="16" /> Назад
        </button>
        <span v-else></span>
        <button v-if="step < 3" class="btn btn-primary" type="button" @click="goNext">
          Далее <AppIcon name="arrow-right" :size="16" />
        </button>
        <button v-else class="btn btn-primary" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>Создать конспект</span>
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import AppIcon from "../components/icons/AppIcon.vue";
import SubjectPicker from "../components/SubjectPicker.vue";
import { api } from "../api/client";

const router = useRouter();
const step = ref(1);
const loading = ref(false);
const error = ref("");
const stepError = ref("");
const subjectMode = ref("catalog");
const tagsInput = ref("");
const groups = ref([]);
const subjects = ref([]);

const steps = [
  { num: 1, label: "Содержание" },
  { num: 2, label: "Настройки" },
  { num: 3, label: "Проверка" }
];

const visOptions = [
  { value: "private", icon: "lock", title: "Приватный", desc: "Только для вас" },
  { value: "public", icon: "globe", title: "Публичный", desc: "Видно всем" },
  { value: "group", icon: "users", title: "Группа", desc: "Только участники" }
];

const form = reactive({
  title: "",
  description: "",
  outline: [{ title: "" }],
  visibility: "private",
  group_id: "",
  subject_id: "",
  subject_custom: ""
});

function addOutline() {
  form.outline.push({ title: "" });
}

function removeOutline(i) {
  form.outline.splice(i, 1);
  if (!form.outline.length) form.outline.push({ title: "" });
}

const previewOutline = computed(() =>
  form.outline
    .map((item, i) => ({ order: i + 1, title: (item.title || "").trim() }))
    .filter((item) => item.title)
);

const previewTags = computed(() =>
  tagsInput.value.split(",").map((t) => t.trim()).filter(Boolean)
);

const visibilityTitle = computed(() => {
  const opt = visOptions.find((v) => v.value === form.visibility);
  return opt ? opt.title : form.visibility;
});

const selectedGroupName = computed(() => groups.value.find((g) => g.id === form.group_id)?.name || "");
const selectedSubjectName = computed(() => {
  if (subjectMode.value === "catalog") {
    return subjects.value.find((s) => s.id === form.subject_id)?.name || "";
  }
  return form.subject_custom;
});

function validate(targetStep) {
  stepError.value = "";
  if (targetStep >= 2 && (!form.title.trim() || !form.description.trim())) {
    stepError.value = "Заполните название и описание.";
    return false;
  }
  if (targetStep >= 3) {
    if (form.visibility === "group" && !form.group_id) {
      stepError.value = "Выберите группу.";
      return false;
    }
    if (subjectMode.value === "catalog" && !form.subject_id) {
      stepError.value = "Выберите предмет из справочника.";
      return false;
    }
    if (subjectMode.value === "custom" && !form.subject_custom.trim()) {
      stepError.value = "Введите название предмета.";
      return false;
    }
  }
  return true;
}

function goNext() {
  if (validate(step.value + 1)) step.value++;
}

async function submit() {
  if (!validate(3)) { step.value = 2; return; }
  loading.value = true;
  error.value = "";
  try {
    const payload = {
      title: form.title,
      description: form.description,
      outline: previewOutline.value,
      visibility: form.visibility,
      group_id: form.visibility === "group" ? form.group_id : null,
      subject_id: subjectMode.value === "catalog" ? form.subject_id : null,
      subject_custom: subjectMode.value === "custom" ? form.subject_custom : null,
      tags: previewTags.value
    };
    const created = await api.createNote(payload);
    await router.push(`/notes/${created.id}`);
  } catch (err) {
    error.value = err.message || "Ошибка создания";
  } finally {
    loading.value = false;
  }
}

async function loadMeta() {
  try {
    const [grps, subs] = await Promise.all([api.myGroups(), api.subjects()]);
    groups.value = grps;
    subjects.value = subs;
  } catch (err) {
    error.value = err.message || "Не удалось загрузить данные";
  }
}

onMounted(loadMeta);
</script>

<style scoped>
.wizard {
  max-width: 680px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}

.wizard-head h1 {
  margin: 0 0 4px;
  font-size: 24px;
}

.wizard-head p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  padding: 0 4px;
}

.stepper::before {
  content: '';
  position: absolute;
  top: 16px;
  left: 24px;
  right: 24px;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
}

.stepper-line {
  position: absolute;
  top: 16px;
  left: 24px;
  height: 3px;
  background: var(--brand-500);
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.stepper-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
  z-index: 1;
}

.stepper-dot {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--surface);
  border: 2.5px solid var(--border);
  font-weight: 700;
  font-size: 14px;
  color: var(--text-muted);
  transition: all var(--transition-base);
}

.stepper-item.active .stepper-dot {
  border-color: var(--brand-500);
  background: var(--brand-500);
  color: white;
  box-shadow: var(--shadow-brand);
}

.stepper-item.done .stepper-dot {
  border-color: var(--success-500);
  background: var(--success-500);
  color: white;
}

.stepper-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.stepper-item.active .stepper-label { color: var(--brand-700); }
.stepper-item.done .stepper-label { color: var(--success-500); }

.wizard-body {
  padding: 28px 24px;
}

.step-content {
  display: grid;
  gap: 18px;
}

.step-enter-active { animation: slide-in-right 0.3s ease; }
.step-leave-active { animation: fade-in 0.15s ease reverse; }

.field {
  display: grid;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.field-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.outline-list {
  display: grid;
  gap: 6px;
}

.outline-row {
  display: flex;
  gap: 6px;
}

.outline-row input { flex: 1; }

.vis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.vis-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 8px;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--surface);
}

.vis-card:hover { border-color: var(--brand-200); }
.vis-card.active {
  border-color: var(--brand-500);
  background: var(--brand-50);
}

.vis-icon {
  color: var(--text-secondary);
}

.vis-card.active .vis-icon {
  color: var(--brand-600);
}
.vis-title { font-weight: 700; font-size: 14px; }
.vis-desc { font-size: 12px; color: var(--text-muted); }

.preview-title {
  margin: 0 0 12px;
  font-size: 18px;
}

.preview-grid {
  display: grid;
  gap: 12px;
}

.preview-item {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 8px;
  font-size: 14px;
}

.preview-label {
  color: var(--text-muted);
  font-weight: 600;
}

.preview-ol {
  margin: 0;
  padding-left: 20px;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

@media (max-width: 600px) {
  .vis-grid { grid-template-columns: 1fr; }
  .preview-item { grid-template-columns: 1fr; gap: 2px; }
}
</style>
