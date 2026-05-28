<template>
  <section class="friends animate-fade-up">
    <form class="card request-card" @submit.prevent="sendRequest">
      <h3>Добавить друга</h3>
      <div class="request-row">
        <input v-model.trim="login" placeholder="Логин пользователя" required minlength="3" maxlength="32" />
        <button class="btn btn-primary btn-sm">Отправить заявку</button>
      </div>
    </form>

    <p v-if="message" class="feedback-ok animate-fade-in">{{ message }}</p>
    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>

    <div class="grid">
      <div class="card panel">
        <h3>Входящие заявки</h3>
        <div v-if="!incoming.length" class="empty-state" style="padding: 16px">Новых заявок нет</div>
        <ul class="req-list">
          <li v-for="r in incoming" :key="r.id">
            <span class="req-name">{{ r.requester_login }}</span>
            <div class="req-actions">
              <button class="btn btn-primary btn-sm" @click="respond(r.id, 'accept')">Принять</button>
              <button class="btn btn-secondary btn-sm" @click="respond(r.id, 'reject')">Отклонить</button>
            </div>
          </li>
        </ul>
      </div>

      <div class="card panel">
        <h3>Друзья</h3>
        <div v-if="!friends.length" class="empty-state" style="padding: 16px">Пока нет друзей</div>
        <ul class="friend-list">
          <li v-for="f in friends" :key="f.user_id" class="friend-item">
            <RouterLink :to="`/users/${f.login}`" class="friend-row">
              <span class="friend-avatar">{{ f.login.charAt(0).toUpperCase() }}</span>
              <span class="friend-name">{{ f.login }}</span>
            </RouterLink>
            <button class="btn btn-danger btn-sm" type="button" @click="removeFriend(f.user_id)">
              Удалить
            </button>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppIcon from "../components/icons/AppIcon.vue";
import { api } from "../api/client";

const login = ref("");
const message = ref("");
const error = ref("");
const incoming = ref([]);
const friends = ref([]);

async function loadData() {
  error.value = "";
  try {
    const [inc, fri] = await Promise.all([api.incomingFriendRequests(), api.friends()]);
    incoming.value = inc;
    friends.value = fri;
  } catch (err) {
    error.value = err.message || "Не удалось загрузить данные";
  }
}

async function sendRequest() {
  error.value = "";
  message.value = "";
  try {
    await api.sendFriendRequest({ login: login.value });
    login.value = "";
    message.value = "Заявка отправлена";
    await loadData();
  } catch (err) {
    error.value = err.message || "Не удалось отправить заявку";
  }
}

async function respond(requestId, action) {
  error.value = "";
  message.value = "";
  try {
    await api.respondFriendRequest(requestId, action);
    message.value = action === "accept" ? "Заявка принята" : "Заявка отклонена";
    await loadData();
  } catch (err) {
    error.value = err.message || "Не удалось обработать заявку";
  }
}

async function removeFriend(userId) {
  if (!window.confirm("Удалить пользователя из друзей?")) return;
  error.value = "";
  message.value = "";
  try {
    await api.removeFriend(userId);
    message.value = "Друг удалён";
    await loadData();
  } catch (err) {
    error.value = err.message || "Не удалось удалить друга";
  }
}

onMounted(loadData);
</script>

<style scoped>
.friends {
  display: grid;
  gap: 16px;
}

.request-card {
  padding: 16px;
}

.request-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.request-row {
  display: flex;
  gap: 8px;
}

.request-row input { flex: 1; max-width: 320px; }

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel {
  padding: 16px;
}

.panel h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.req-list, .friend-list {
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
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.req-name { font-weight: 600; }

.req-actions { display: flex; gap: 6px; }

.friend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 8px 6px 0;
  transition: all var(--transition-fast);
}

.friend-item:hover {
  border-color: var(--brand-200);
  background: var(--surface-muted);
}

.friend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  text-decoration: none;
  color: inherit;
  flex: 1;
}

.friend-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-400), var(--accent-500));
  color: white;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.friend-name { font-weight: 600; flex: 1; }

@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
  .request-row { flex-direction: column; }
  .request-row input { max-width: 100%; }
}
</style>
