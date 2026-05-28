<template>
  <section class="user-notes animate-fade-up">
    <header class="card head-card">
      <div>
        <h1>Конспекты {{ login }}</h1>
        <p>Видимые вам опубликованные конспекты пользователя</p>
      </div>
      <div class="filters">
        <input v-model.trim="subject" placeholder="Фильтр по предмету" />
        <select v-model="sort">
          <option value="-created_at">Новые</option>
          <option value="created_at">Старые</option>
        </select>
        <button class="btn btn-secondary btn-sm" @click="loadNotes">Применить</button>
      </div>
    </header>

    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>
    <div v-if="loading" class="loading-spinner">Загрузка…</div>

    <div class="notes-grid" v-if="notes.length">
      <article v-for="n in notes" :key="n.id" class="card card-interactive note-card">
        <RouterLink :to="`/notes/${n.id}`" class="note-link">
          <h3>{{ n.title }}</h3>
          <p>{{ n.description || 'Без описания' }}</p>
          <div class="note-meta">
            <span class="badge badge-brand">{{ n.subject_name || n.subject_custom || 'Без предмета' }}</span>
            <span class="badge badge-muted">{{ n.visibility }}</span>
          </div>
        </RouterLink>
      </article>
    </div>
    <div v-else-if="!loading" class="empty-state">Нет конспектов по текущим фильтрам</div>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { api } from "../api/client";

const route = useRoute();
const login = ref(route.params.login);
const subject = ref("");
const sort = ref("-created_at");
const notes = ref([]);
const loading = ref(false);
const error = ref("");

async function loadNotes() {
  loading.value = true;
  error.value = "";
  try {
    notes.value = await api.userNotes(login.value, {
      subject: subject.value || undefined,
      sort: sort.value
    });
  } catch (err) {
    error.value = err.message || "Не удалось загрузить конспекты";
    notes.value = [];
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.login, (newLogin) => {
  if (newLogin && newLogin !== login.value) {
    login.value = newLogin;
    loadNotes();
  }
});

onMounted(loadNotes);
</script>

<style scoped>
.user-notes {
  display: grid;
  gap: 16px;
}

.head-card {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.head-card h1 { margin: 0 0 4px; font-size: 22px; }
.head-card p { margin: 0; color: var(--text-secondary); font-size: 14px; }

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.notes-grid {
  display: grid;
  gap: 12px;
}

.note-card {
  transition: all var(--transition-base);
}

.note-link {
  display: block;
  padding: 16px 18px;
  text-decoration: none;
  color: inherit;
}

.note-link h3 { margin: 0 0 4px; font-size: 16px; }
.note-link p { margin: 0 0 8px; font-size: 14px; color: var(--text-secondary); }

.note-meta { display: flex; gap: 6px; }

@media (max-width: 640px) {
  .head-card { flex-direction: column; align-items: flex-start; }
  .filters { width: 100%; }
}
</style>
