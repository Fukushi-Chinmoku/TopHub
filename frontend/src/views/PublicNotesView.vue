<template>
  <section class="explore animate-fade-up">
    <header class="hero card">
      <div>
        <h1>Конспекты</h1>
        <p class="hero-sub">Все опубликованные публичные конспекты платформы</p>
      </div>
    </header>

    <div class="filters card">
      <div class="filter-subject">
        <label class="filter-label">Предмет</label>
        <SubjectPicker v-model:subject-id="subjectId" variant="filter" />
      </div>
      <input v-model.trim="searchQuery" placeholder="Поиск по названию или описанию…" />
      <select v-model="sort">
        <option value="-created_at">Сначала новые</option>
        <option value="created_at">Сначала старые</option>
      </select>
      <button class="btn btn-secondary btn-sm" @click="loadNotes">Применить</button>
    </div>

    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>

    <div class="notes-grid" v-if="notes.length">
      <article
        v-for="(note, i) in notes"
        :key="note.id"
        class="note-card card card-interactive"
        :style="{ animationDelay: `${i * 50}ms` }"
      >
        <RouterLink class="note-link" :to="`/notes/${note.id}`">
          <div class="note-top">
            <h3>{{ note.title }}</h3>
            <span class="badge badge-success">Публичный</span>
          </div>
          <p class="note-desc">{{ note.description || "Без описания" }}</p>
          <div class="note-meta">
            <span class="badge badge-brand">{{ note.subject_name || note.subject_custom || "Без предмета" }}</span>
            <span v-if="note.owner_login" class="badge badge-muted">
              {{ note.owner_display_name || note.owner_login }}
            </span>
            <span class="badge badge-muted">★ {{ note.rating_avg.toFixed(1) }}</span>
          </div>
          <div class="note-tags" v-if="note.tags?.length">
            <span v-for="tag in note.tags" :key="tag" class="tag">#{{ tag }}</span>
          </div>
        </RouterLink>
      </article>
    </div>
    <div v-else class="empty-state">
      <p>Публичных конспектов не найдено</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import SubjectPicker from "../components/SubjectPicker.vue";
import { api } from "../api/client";

const subjectId = ref("");
const searchQuery = ref("");
const sort = ref("-created_at");
const error = ref("");
const notes = ref([]);

async function loadNotes() {
  error.value = "";
  try {
    notes.value = await api.publicNotes({
      subject_id: subjectId.value || undefined,
      q: searchQuery.value || undefined,
      sort: sort.value
    });
  } catch (err) {
    error.value = err.message || "Не удалось загрузить конспекты";
  }
}

onMounted(loadNotes);
</script>

<style scoped>
.explore {
  display: grid;
  gap: 20px;
}

.hero {
  padding: 24px;
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
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
