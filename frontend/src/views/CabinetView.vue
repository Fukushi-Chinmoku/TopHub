<template>
  <section class="cabinet animate-fade-up">
    <header class="hero card">
      <div class="hero-content">
        <h1>Личный кабинет</h1>
        <p class="hero-sub">Управляйте конспектами, следите за рейтингом и публикациями</p>
      </div>
      <div class="hero-rating">
        <div class="rating-value">{{ cabinet.rating_avg.toFixed(1) }}</div>
        <div class="rating-label">Средний рейтинг</div>
        <div class="rating-meta">{{ cabinet.rating_count }} оценок</div>
      </div>
    </header>

    <div class="metrics">
      <article class="metric card">
        <span class="metric-number">{{ cabinet.notes.length }}</span>
        <span class="metric-label">Всего</span>
      </article>
      <article class="metric card" style="--accent: var(--success-500)">
        <span class="metric-number">{{ publishedCount }}</span>
        <span class="metric-label">Опубликовано</span>
      </article>
    </div>

    <div class="filters card">
      <div class="filter-subject">
        <label class="filter-label">Предмет</label>
        <SubjectPicker v-model:subject-id="subjectId" variant="filter" />
      </div>
      <select v-model="visibility">
        <option value="">Все видимости</option>
        <option value="private">Приватные</option>
        <option value="public">Публичные</option>
        <option value="group">Групповые</option>
      </select>
      <select v-model="sort">
        <option value="-created_at">Сначала новые</option>
        <option value="created_at">Сначала старые</option>
      </select>
      <button class="btn btn-secondary btn-sm" @click="loadCabinet">Применить</button>
    </div>

    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>

    <div class="notes-grid" v-if="cabinet.notes.length">
      <article
        v-for="(note, i) in cabinet.notes"
        :key="note.id"
        class="note-card card card-interactive"
        :style="{ animationDelay: `${i * 50}ms` }"
      >
        <div class="note-card-inner">
          <RouterLink class="note-link" :to="`/notes/${note.id}`">
            <div class="note-top">
              <h3>{{ note.title }}</h3>
              <span :class="['badge', note.is_published ? 'badge-success' : 'badge-warn']">
                {{ note.is_published ? 'Опубликован' : 'Черновик' }}
              </span>
            </div>
            <p class="note-desc">{{ note.description || 'Без описания' }}</p>
            <div class="note-meta">
              <span class="badge badge-muted">{{ visibilityLabel(note.visibility) }}</span>
              <span class="badge badge-brand">{{ note.subject_name || note.subject_custom || 'Без предмета' }}</span>
            </div>
            <div class="note-tags" v-if="note.tags?.length">
              <span v-for="tag in note.tags" :key="tag" class="tag">#{{ tag }}</span>
            </div>
          </RouterLink>
          <button class="btn btn-danger btn-sm note-delete" type="button" @click="deleteNote(note.id)">
            Удалить
          </button>
        </div>
      </article>
    </div>
    <div v-else class="empty-state">
      <p>У вас пока нет конспектов</p>
      <RouterLink class="btn btn-primary" to="/notes/new" style="margin-top: 12px">
        <AppIcon name="plus" :size="16" /> Создать первый конспект
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import AppIcon from "../components/icons/AppIcon.vue";
import SubjectPicker from "../components/SubjectPicker.vue";
import { api } from "../api/client";

const subjectId = ref("");
const visibility = ref("");
const sort = ref("-created_at");
const error = ref("");
const cabinet = reactive({ user_id: "", rating_avg: 0, rating_count: 0, notes: [] });

const publishedCount = computed(() => cabinet.notes.filter((n) => n.is_published).length);

function visibilityLabel(v) {
  if (v === "public") return "Публичный";
  if (v === "group") return "Группа";
  return "Приватный";
}

async function loadCabinet() {
  error.value = "";
  try {
    const data = await api.cabinet({
      subject_id: subjectId.value || undefined,
      visibility: visibility.value || undefined,
      sort: sort.value
    });
    Object.assign(cabinet, data);
  } catch (err) {
    error.value = err.message || "Не удалось загрузить кабинет";
  }
}

async function deleteNote(noteId) {
  if (!window.confirm("Удалить конспект без возможности восстановления?")) return;
  error.value = "";
  try {
    await api.deleteNote(noteId);
    await loadCabinet();
  } catch (err) {
    error.value = err.message || "Не удалось удалить конспект";
  }
}

onMounted(loadCabinet);
</script>

<style scoped>
.cabinet {
  display: grid;
  gap: 20px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 24px;
  background: linear-gradient(135deg, var(--brand-50), var(--surface));
}

.hero h1 {
  margin: 0 0 4px;
  font-size: 24px;
}

.hero-sub {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.hero-rating {
  text-align: center;
  flex-shrink: 0;
}

.rating-value {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--brand-500), var(--accent-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
}

.rating-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.rating-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.metric {
  padding: 16px;
  text-align: center;
  border-left: 3px solid var(--accent, var(--brand-500));
}

.metric-number {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.metric-label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
}

.filter-subject {
  display: grid;
  gap: 4px;
  min-width: 180px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.filters input,
.filters select {
  min-width: 140px;
}

.note-card-inner {
  position: relative;
}

.note-delete {
  margin: 0 16px 16px;
}

.notes-grid {
  display: grid;
  gap: 12px;
}

.note-card {
  animation: fade-up 0.35s ease both;
}

.note-link {
  display: block;
  padding: 18px 20px;
  text-decoration: none;
  color: inherit;
}

.note-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.note-top h3 {
  margin: 0;
  font-size: 16px;
}

.note-desc {
  margin: 6px 0 10px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.note-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.note-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

@media (max-width: 640px) {
  .hero {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .metrics {
    grid-template-columns: 1fr;
  }

  .filters {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
