<template>
  <section class="groups animate-fade-up">
    <div class="top-actions">
      <form class="card action-card" @submit.prevent="createGroup">
        <h3>Создать группу</h3>
        <div class="action-row">
          <input v-model.trim="createName" placeholder="Название группы" required minlength="3" />
          <button class="btn btn-primary btn-sm">Создать</button>
        </div>
      </form>
      <form class="card action-card" @submit.prevent="joinGroup">
        <h3>Вступить в группу</h3>
        <div class="action-row">
          <input v-model.trim="joinName" placeholder="Название группы" required minlength="3" />
          <button class="btn btn-secondary btn-sm">Отправить заявку</button>
        </div>
      </form>
    </div>

    <p v-if="message" class="feedback-ok animate-fade-in">{{ message }}</p>
    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>

    <div class="content-layout">
      <aside class="card sidebar">
        <h3>Мои группы</h3>
        <div v-if="!groups.length" class="empty-state" style="padding: 16px">Вы не состоите в группах</div>
        <button
          v-for="g in groups"
          :key="g.id"
          :class="['group-btn', { active: selectedGroup?.id === g.id }]"
          @click="selectGroup(g)"
        >
          <AppIcon name="groups" :size="18" class="group-icon" />
          {{ g.name }}
        </button>
      </aside>

      <div class="main-area" v-if="selectedGroup">
        <div class="card detail-card">
          <div class="detail-header">
            <h2>{{ selectedGroup.name }}</h2>
            <div class="detail-header-right">
              <div class="detail-stats">
                <span class="badge badge-brand">{{ members.length }} участников</span>
                <span class="badge badge-muted">{{ notes.length }} конспектов</span>
              </div>
              <button
                v-if="!isOwner"
                class="btn btn-secondary btn-sm"
                type="button"
                @click="leaveGroup"
              >
                Выйти из группы
              </button>
              <button
                v-else
                class="btn btn-danger btn-sm"
                type="button"
                @click="deleteGroup"
              >
                Удалить группу
              </button>
            </div>
          </div>

          <div class="filters-row">
            <div class="filter-subject">
              <label class="filter-label">Предмет</label>
              <SubjectPicker v-model:subject-id="subjectId" variant="filter" />
            </div>
            <select v-model="author">
              <option value="">Все авторы</option>
              <option v-for="m in members" :key="m.user_id" :value="m.user_id">{{ m.login }}</option>
            </select>
            <select v-model="sort">
              <option value="-created_at">Новые</option>
              <option value="created_at">Старые</option>
            </select>
            <button class="btn btn-secondary btn-sm" @click="loadGroupNotes">Применить</button>
          </div>

          <section v-if="isOwner" class="requests-block">
            <h4>Входящие заявки</h4>
            <div v-if="!joinRequests.length" class="empty-state" style="padding: 12px">
              Новых заявок на вступление нет
            </div>
            <ul v-else class="req-list">
              <li v-for="req in joinRequests" :key="req.user_id">
                <div class="req-info">
                  <strong>{{ req.login }}</strong>
                  <span class="req-meta">{{ req.display_name }}</span>
                </div>
                <div class="req-actions">
                  <button class="btn btn-primary btn-sm" @click="respondJoin(req.user_id, 'accept')">
                    Принять
                  </button>
                  <button class="btn btn-secondary btn-sm" @click="respondJoin(req.user_id, 'reject')">
                    Отклонить
                  </button>
                </div>
              </li>
            </ul>
          </section>

          <div class="split-view">
            <div class="members-col">
              <h4>Участники</h4>
              <ul class="member-list">
                <li v-for="m in members" :key="m.user_id">
                  <RouterLink :to="`/users/${m.login}`" class="member-link">{{ m.login }}</RouterLink>
                  <span class="badge badge-muted">{{ m.role }}</span>
                </li>
              </ul>
            </div>
            <div class="notes-col">
              <h4>Конспекты</h4>
              <div v-if="!notes.length" class="empty-state" style="padding: 16px">Нет конспектов</div>
              <ul class="note-list">
                <li v-for="n in notes" :key="n.id" class="note-item">
                  <RouterLink :to="`/notes/${n.id}`" class="note-link-inner">
                    <strong>{{ n.title }}</strong>
                    <span class="note-subj">{{ n.subject_name || n.subject_custom || 'Без предмета' }}</span>
                  </RouterLink>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppIcon from "../components/icons/AppIcon.vue";
import SubjectPicker from "../components/SubjectPicker.vue";
import { api } from "../api/client";
import { useAuth } from "../state/auth";

const auth = useAuth();
const groups = ref([]);
const selectedGroup = ref(null);
const members = ref([]);
const joinRequests = ref([]);
const notes = ref([]);

const isOwner = computed(() => {
  if (!selectedGroup.value || !auth.state.user) return false;
  return String(selectedGroup.value.owner_id) === String(auth.state.user.id);
});
const createName = ref("");
const joinName = ref("");
const subjectId = ref("");
const author = ref("");
const sort = ref("-created_at");
const message = ref("");
const error = ref("");

async function loadGroups() {
  try {
    groups.value = await api.myGroups();
    if (!selectedGroup.value && groups.value.length) await selectGroup(groups.value[0]);
  } catch (err) {
    error.value = err.message || "Не удалось загрузить группы";
  }
}

async function loadJoinRequests() {
  if (!selectedGroup.value || !isOwner.value) {
    joinRequests.value = [];
    return;
  }
  try {
    joinRequests.value = await api.groupJoinRequests(selectedGroup.value.id);
  } catch (err) {
    joinRequests.value = [];
    if (err.message && !err.message.includes("403")) {
      error.value = err.message;
    }
  }
}

async function selectGroup(g) {
  error.value = "";
  try {
    selectedGroup.value = g;
    members.value = await api.groupMembers(g.id);
    await Promise.all([loadGroupNotes(), loadJoinRequests()]);
  } catch (err) {
    error.value = err.message || "Не удалось открыть группу";
  }
}

async function respondJoin(userId, action) {
  if (!selectedGroup.value) return;
  error.value = "";
  message.value = "";
  try {
    await api.respondGroupJoinRequest(selectedGroup.value.id, userId, action);
    message.value = action === "accept" ? "Заявка принята" : "Заявка отклонена";
    members.value = await api.groupMembers(selectedGroup.value.id);
    await loadJoinRequests();
  } catch (err) {
    error.value = err.message || "Не удалось обработать заявку";
  }
}

async function loadGroupNotes() {
  if (!selectedGroup.value) return;
  error.value = "";
  try {
    notes.value = await api.groupNotes(selectedGroup.value.id, {
      subject_id: subjectId.value || undefined,
      author: author.value || undefined,
      sort: sort.value
    });
  } catch (err) {
    error.value = err.message || "Не удалось загрузить конспекты";
  }
}

async function createGroup() {
  error.value = "";
  message.value = "";
  try {
    await api.createGroup({ name: createName.value });
    createName.value = "";
    message.value = "Группа создана";
    await loadGroups();
  } catch (err) {
    error.value = err.message || "Не удалось создать группу";
  }
}

async function joinGroup() {
  error.value = "";
  message.value = "";
  try {
    await api.joinGroup({ name: joinName.value });
    joinName.value = "";
    message.value = "Заявка отправлена";
  } catch (err) {
    error.value = err.message || "Не удалось отправить заявку";
  }
}

async function leaveGroup() {
  if (!selectedGroup.value) return;
  if (!window.confirm(`Выйти из группы «${selectedGroup.value.name}»?`)) return;
  error.value = "";
  message.value = "";
  try {
    await api.leaveGroup(selectedGroup.value.id);
    message.value = "Вы вышли из группы";
    selectedGroup.value = null;
    members.value = [];
    notes.value = [];
    joinRequests.value = [];
    await loadGroups();
  } catch (err) {
    error.value = err.message || "Не удалось выйти из группы";
  }
}

async function deleteGroup() {
  if (!selectedGroup.value) return;
  if (
    !window.confirm(
      `Удалить группу «${selectedGroup.value.name}»? Групповые конспекты станут приватными у их авторов.`
    )
  ) {
    return;
  }
  error.value = "";
  message.value = "";
  try {
    await api.deleteGroup(selectedGroup.value.id);
    message.value = "Группа удалена";
    selectedGroup.value = null;
    members.value = [];
    notes.value = [];
    joinRequests.value = [];
    await loadGroups();
  } catch (err) {
    error.value = err.message || "Не удалось удалить группу";
  }
}

onMounted(loadGroups);
</script>

<style scoped>
.groups {
  display: grid;
  gap: 16px;
}

.top-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.action-card {
  padding: 16px;
}

.action-card h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.action-row {
  display: flex;
  gap: 8px;
}

.action-row input { flex: 1; }

.content-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
}

.sidebar {
  padding: 16px;
  display: grid;
  align-content: start;
  gap: 6px;
}

.sidebar h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.group-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-weight: 500;
  font-size: 14px;
  text-align: left;
  transition: all var(--transition-fast);
}

.group-btn:hover { border-color: var(--brand-200); background: var(--surface-muted); }
.group-btn.active {
  border-color: var(--brand-500);
  background: var(--brand-50);
  color: var(--brand-700);
  font-weight: 600;
}

.group-icon {
  color: var(--text-muted);
}

.group-btn.active .group-icon {
  color: var(--brand-600);
}

.detail-card { padding: 20px; }

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h2 { margin: 0; font-size: 20px; }

.detail-header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.detail-stats { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }

.filters-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 16px;
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

.requests-block {
  margin-bottom: 16px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--brand-50);
}

.requests-block h4 {
  margin: 0 0 10px;
}

.req-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.req-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.req-info {
  display: grid;
  gap: 2px;
}

.req-info strong {
  font-size: 14px;
}

.req-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.req-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.split-view {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
}

h4 { margin: 0 0 8px; font-size: 14px; color: var(--text-secondary); }

.member-list, .note-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.member-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
}

.member-link {
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.note-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.note-item:hover { border-color: var(--brand-200); }

.note-link-inner {
  display: block;
  padding: 10px 12px;
  text-decoration: none;
  color: inherit;
}

.note-link-inner strong { display: block; margin-bottom: 2px; }
.note-subj { font-size: 13px; color: var(--text-muted); }

@media (max-width: 860px) {
  .top-actions, .content-layout, .split-view { grid-template-columns: 1fr; }
}
</style>
