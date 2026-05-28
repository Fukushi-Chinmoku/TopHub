<template>
  <section v-if="!ready" class="loading-page animate-fade-in">
    <div v-if="loadError" class="card error-card">
      <h2>Не удалось загрузить конспект</h2>
      <p class="text-danger">{{ loadError }}</p>
      <RouterLink class="btn btn-primary" to="/cabinet">Вернуться в кабинет</RouterLink>
    </div>
    <div v-else class="loading-spinner">Загрузка конспекта…</div>
  </section>

  <section v-else class="note-page animate-fade-up">
    <header class="note-header card">
      <div class="header-top">
        <div class="header-info">
          <h1>{{ form.title || 'Новый конспект' }}</h1>
          <div class="header-badges">
            <span :class="['badge', note.is_published ? 'badge-success' : 'badge-warn']">
              {{ note.is_published ? 'Опубликован' : 'Черновик' }}
            </span>
            <span :class="['badge', wsStatus === 'online' ? 'badge-success' : 'badge-muted']">
              {{ wsStatus === 'online' ? 'В сети' : 'Нет соединения' }}
            </span>
            <span :class="['badge', syncStatus === 'syncing' ? 'badge-warn' : 'badge-muted']">
              {{ autosaveLabel }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" :disabled="note.is_published" @click="publish">
            {{ note.is_published ? 'Опубликован' : 'Опубликовать' }}
          </button>
          <button v-if="isOwner" class="btn btn-danger btn-sm" type="button" @click="deleteNote">
            Удалить конспект
          </button>
        </div>
      </div>

      <div class="presence-bar" v-if="onlineUsers.length">
        <span class="presence-label">В документе:</span>
        <span v-for="u in onlineUsers" :key="u.id" class="presence-user">
          <span class="presence-dot" :style="{ background: u.color || colorFromId(String(u.id)) }"></span>
          {{ u.name }}{{ u.isSelf ? ' (вы)' : '' }}
        </span>
      </div>
    </header>

    <div class="tabs-row">
      <button :class="['tab-btn', { active: activeTab === 'editor' }]" @click="activeTab = 'editor'">Редактор</button>
      <button :class="['tab-btn', { active: activeTab === 'meta' }]" @click="activeTab = 'meta'">Свойства</button>
      <button
        v-if="note.is_published"
        :class="['tab-btn', { active: activeTab === 'discuss' }]"
        @click="activeTab = 'discuss'"
      >
        Обсуждение
      </button>
      <button :class="['tab-btn', { active: activeTab === 'history' }]" @click="activeTab = 'history'">
        Контрольные точки ({{ revisions.length }})
      </button>
    </div>

    <transition name="page" mode="out-in">
      <div v-if="activeTab === 'editor'" key="editor" class="tab-panel card editor-panel">
        <p v-if="activeEditors.length" class="live-editors">
          Сейчас редактируют:
          <span
            v-for="editorUser in activeEditors"
            :key="editorUser.id"
            class="live-editor-chip"
            :style="{ '--chip-color': editorUser.color }"
          >
            {{ editorUser.name }}
          </span>
        </p>
        <RichEditor
          v-if="editorReady && currentUser"
          :key="editorEpoch"
          ref="editorRef"
          v-model="content"
          :ydoc="ydoc"
          :awareness="awareness"
          :current-user="currentUser"
        />
        <div v-else class="loading-spinner">Подключение редактора…</div>
      </div>

      <div v-else-if="activeTab === 'meta'" key="meta" class="tab-panel card">
        <div class="meta-actions">
          <button class="btn btn-secondary" @click="saveMeta">Сохранить свойства</button>
        </div>
        <div class="meta-grid">
          <div class="field field-full">
            <label>Предмет</label>
            <SubjectPicker
              v-model:mode="subjectMode"
              v-model:subject-id="metaSubjectId"
              v-model:subject-custom="metaSubjectCustom"
            />
          </div>
          <div class="field">
            <label>Название</label>
            <input v-model.trim="form.title" />
          </div>
          <div class="field">
            <label>Описание</label>
            <textarea v-model.trim="form.description" rows="2" />
          </div>
          <div class="field">
            <label>Видимость</label>
            <select v-model="form.visibility">
              <option value="private">Приватный</option>
              <option value="public">Публичный</option>
              <option value="group">Только группа</option>
            </select>
          </div>
          <div class="field" v-if="form.visibility === 'group'">
            <label>Группа</label>
            <select v-model="form.group_id">
              <option disabled value="">Выберите группу</option>
              <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>Теги</label>
            <input v-model="tagsInput" placeholder="tag1, tag2" />
          </div>
          <div class="field">
            <div class="field-row">
              <label>Оглавление</label>
              <button class="btn btn-ghost btn-sm" type="button" @click="addOutlineItem">
                <AppIcon name="plus" :size="14" /> Пункт
              </button>
            </div>
            <div v-if="!form.outline.length" class="empty-state" style="padding: 12px">Пусто</div>
            <div v-for="(item, i) in form.outline" :key="i" class="outline-row">
              <input v-model.trim="item.title" :placeholder="`Пункт ${item.order}`" />
              <button class="btn btn-ghost btn-sm" type="button" aria-label="Удалить пункт" @click="removeOutlineItem(i)">
                <AppIcon name="close" :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'discuss'" key="discuss" class="tab-panel card">
        <div class="engage-grid">
          <div class="rating-section">
            <h3>Оценка</h3>
            <div class="rating-display">
              <span class="rating-big">{{ rating.rating_avg.toFixed(1) }}</span>
              <span class="rating-count">{{ rating.rating_count }} оценок</span>
            </div>
            <div class="stars">
              <button
                v-for="s in [1,2,3,4,5]"
                :key="s"
                :class="['star', { active: rating.my_score && s <= rating.my_score }]"
                :aria-label="`Оценка ${s}`"
                @click="setRating(s)"
              >
                <AppIcon
                  :name="rating.my_score && s <= rating.my_score ? 'star' : 'star-outline'"
                  :size="22"
                  :filled="Boolean(rating.my_score && s <= rating.my_score)"
                />
              </button>
            </div>
          </div>
          <div class="comments-section">
            <h3>Комментарии ({{ comments.length }})</h3>
            <form class="comment-form" @submit.prevent="sendComment">
              <textarea v-model="commentText" placeholder="Ваш комментарий…" rows="2" />
              <button class="btn btn-secondary btn-sm" :disabled="commentLoading || !commentText.trim()">
                {{ commentLoading ? 'Отправка…' : 'Отправить' }}
              </button>
            </form>
            <ul class="comments-list" v-if="comments.length">
              <li v-for="c in comments" :key="c.id" class="comment-item">
                <div class="comment-author">{{ c.display_name }} ({{ c.login }})</div>
                <div class="comment-body">{{ c.content }}</div>
              </li>
            </ul>
            <div v-else class="empty-state" style="padding: 16px">Комментариев пока нет</div>
          </div>
        </div>
      </div>

      <div v-else key="history" class="tab-panel card">
        <p class="history-hint">
          Текст сохраняется автоматически при редактировании. Здесь только ручные контрольные точки для отката.
        </p>
        <div class="revision-header">
          <h3>Контрольные точки</h3>
          <button class="btn btn-secondary btn-sm" @click="createRevision">Сохранить контрольную точку</button>
        </div>
        <ul class="revision-list" v-if="revisions.length">
          <li v-for="rev in revisions" :key="rev.id" class="revision-item">
            <span class="revision-date">{{ formatDate(rev.created_at) }}</span>
            <div class="revision-actions">
              <button class="btn btn-secondary btn-sm" @click="restoreRevision(rev.id)">Восстановить</button>
              <button class="btn btn-danger btn-sm" @click="deleteRevision(rev.id)">
                <AppIcon name="trash" :size="14" /> Удалить
              </button>
            </div>
          </li>
        </ul>
        <div v-else class="empty-state" style="padding: 16px">Контрольных точек ещё нет</div>
      </div>
    </transition>

    <p v-if="message" class="feedback-ok animate-fade-in">{{ message }}</p>
    <p v-if="error" class="text-danger animate-fade-in">{{ error }}</p>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import * as Y from "yjs";
import * as awarenessProtocol from "y-protocols/awareness";
import { api } from "../api/client";
import AppIcon from "../components/icons/AppIcon.vue";
import RichEditor from "../components/RichEditor.vue";
import SubjectPicker from "../components/SubjectPicker.vue";
import { useAuth } from "../state/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const noteId = route.params.id;
let ydoc = new Y.Doc();
let awareness = new awarenessProtocol.Awareness(ydoc);
const editorRef = ref(null);

const ready = ref(false);
const editorReady = ref(false);
const editorEpoch = ref(0);
const loadError = ref("");
const message = ref("");
const error = ref("");
const activeTab = ref("editor");
const note = reactive({ is_published: false, owner_id: "" });
const subjectMode = ref("catalog");
const metaSubjectId = ref("");
const metaSubjectCustom = ref("");
const rating = reactive({ rating_avg: 0, rating_count: 0, my_score: null });
const groups = ref([]);
const tagsInput = ref("");
const content = ref("");
const comments = ref([]);
const commentText = ref("");
const commentLoading = ref(false);
const wsStatus = ref("offline");
const syncStatus = ref("idle");
const lastSavedAt = ref("");
const presenceUsers = ref([]);
const awarenessTick = ref(0);
const revisions = ref([]);
const currentUser = ref(null);
let ws = null;
let debounceTimer = null;
let yjsUpdateHandler = null;
let awarenessUpdateHandler = null;
let lastSnapshotSentAt = 0;
let syncResolver = null;
let reconnectTimer = null;
let reconnectAttempt = 0;

const autosaveLabel = computed(() => {
  if (wsStatus.value !== "online") {
    return "Автосохранение недоступно";
  }
  if (syncStatus.value === "syncing") {
    return "Сохранение…";
  }
  if (lastSavedAt.value) {
    return `Сохранено в ${lastSavedAt.value}`;
  }
  return "Изменения синхронизируются";
});

const onlineUsers = computed(() => {
  awarenessTick.value;
  const merged = new Map();
  for (const user of presenceUsers.value) {
    merged.set(String(user.id), {
      id: String(user.id),
      name: user.display_name || user.login,
      color: colorFromId(String(user.id)),
      isSelf: String(user.id) === String(currentUser.value?.id)
    });
  }
  for (const [, state] of awareness.getStates()) {
    const user = state?.user;
    if (!user?.id || !user?.name) {
      continue;
    }
    merged.set(String(user.id), {
      id: String(user.id),
      name: user.name,
      color: user.color || colorFromId(String(user.id)),
      isSelf: String(user.id) === String(currentUser.value?.id)
    });
  }
  return [...merged.values()];
});

const activeEditors = computed(() => onlineUsers.value.filter((user) => !user.isSelf));
const isOwner = computed(() => {
  if (!auth.state.user?.id || !note.owner_id) return false;
  return String(note.owner_id) === String(auth.state.user.id);
});
const form = reactive({
  title: "",
  description: "",
  visibility: "private",
  group_id: "",
  outline: []
});

function fill(data) {
  note.is_published = data.is_published;
  note.owner_id = data.owner_id;
  form.title = data.title;
  form.description = data.description;
  form.visibility = data.visibility;
  form.group_id = data.group_id || "";
  form.outline = Array.isArray(data.outline)
    ? data.outline
        .map((item) => ({ order: Number(item?.order) || 1, title: (item?.title || "").trim() }))
        .filter((item) => item.title)
    : [];
  tagsInput.value = (data.tags || []).join(", ");
  content.value = data.content_html || "";
  if (data.subject_custom) {
    subjectMode.value = "custom";
    metaSubjectId.value = "";
    metaSubjectCustom.value = data.subject_custom;
  } else {
    subjectMode.value = "catalog";
    metaSubjectId.value = data.subject_id || "";
    metaSubjectCustom.value = "";
  }
}

function finishInitialSync() {
  if (!syncResolver) {
    return;
  }
  const resolve = syncResolver;
  syncResolver = null;
  resolve();
}

function waitInitialSync() {
  return new Promise((resolve) => {
    syncResolver = resolve;
    setTimeout(finishInitialSync, 4000);
  });
}

function setupAwarenessUser() {
  if (!currentUser.value) {
    return;
  }
  awareness.setLocalStateField("user", {
    id: currentUser.value.id,
    name: currentUser.value.name,
    color: currentUser.value.color
  });
}

function resetCollaborationDoc(html = "") {
  if (yjsUpdateHandler) {
    ydoc.off("update", yjsUpdateHandler);
    yjsUpdateHandler = null;
  }
  if (awarenessUpdateHandler) {
    awareness.off("update", awarenessUpdateHandler);
    awarenessUpdateHandler = null;
  }
  awareness.destroy();
  ydoc.destroy();
  ydoc = new Y.Doc();
  awareness = new awarenessProtocol.Awareness(ydoc);
  content.value = html;
  editorReady.value = false;
  editorEpoch.value += 1;
  setupAwarenessUser();
}

async function load() {
  try {
    const [noteData, myGroups, meData] = await Promise.all([api.note(noteId), api.myGroups(), api.me()]);
    const me = meData.user;
    currentUser.value = {
      id: String(me.id),
      name: me.display_name || me.login,
      color: colorFromId(String(me.id))
    };
    setupAwarenessUser();
    groups.value = myGroups;
    fill(noteData);
    await loadEngagement();
    await loadRevisions();
    connectSocket();
    await waitInitialSync();
    editorReady.value = true;
    ready.value = true;
    bindYjsUpdates();
    bindAwarenessUpdates();
  } catch (err) {
    loadError.value = err.message || "Не удалось загрузить конспект";
  }
}

async function saveMeta() {
  error.value = "";
  message.value = "";
  try {
    const updated = await api.updateNote(noteId, {
      title: form.title,
      description: form.description,
      visibility: form.visibility,
      group_id: form.visibility === "group" ? form.group_id : null,
      subject_id: subjectMode.value === "catalog" ? metaSubjectId.value || null : null,
      subject_custom: subjectMode.value === "custom" ? metaSubjectCustom.value.trim() || null : null,
      outline: form.outline
        .map((item, i) => ({ order: i + 1, title: (item.title || "").trim() }))
        .filter((item) => item.title),
      tags: tagsInput.value.split(",").map((t) => t.trim()).filter(Boolean)
    });
    fill(updated);
    message.value = "Свойства сохранены";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка сохранения свойств";
  }
}

function clearMsg() {
  setTimeout(() => { message.value = ""; }, 3000);
}

function addOutlineItem() {
  form.outline.push({ order: form.outline.length + 1, title: "" });
}

function removeOutlineItem(i) {
  form.outline.splice(i, 1);
  form.outline = form.outline.map((item, idx) => ({ ...item, order: idx + 1 }));
}

async function deleteNote() {
  if (!window.confirm("Удалить конспект без возможности восстановления?")) return;
  error.value = "";
  try {
    await api.deleteNote(noteId);
    await router.push("/cabinet");
  } catch (err) {
    error.value = err.message || "Не удалось удалить конспект";
  }
}

async function publish() {
  error.value = "";
  message.value = "";
  try {
    const updated = await api.publishNote(noteId);
    fill(updated);
    await loadEngagement();
    await loadRevisions();
    message.value = "Конспект опубликован";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка публикации";
  }
}

function scheduleReconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }
  const delay = Math.min(1000 * 2 ** reconnectAttempt, 10000);
  reconnectAttempt += 1;
  reconnectTimer = setTimeout(() => {
    connectSocket();
  }, delay);
}

function connectSocket() {
  if (ws) {
    ws.onclose = null;
    ws.close();
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${protocol}://${window.location.host}/ws/notes/${noteId}`);
  ws.onopen = () => {
    wsStatus.value = "online";
    reconnectAttempt = 0;
    const localState = awareness.getLocalState();
    if (localState) {
      const update = awarenessProtocol.encodeAwarenessUpdate(awareness, [awareness.clientID]);
      ws.send(
        JSON.stringify({
          type: "awareness_update",
          note_id: noteId,
          awareness_client_id: awareness.clientID,
          awareness_update_base64: toBase64(update)
        })
      );
    }
  };
  ws.onclose = () => {
    wsStatus.value = "offline";
    syncStatus.value = "offline";
    scheduleReconnect();
  };
  ws.onerror = () => {
    wsStatus.value = "offline";
    syncStatus.value = "offline";
  };
  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === "presence") {
        presenceUsers.value = Array.isArray(payload.users) ? payload.users : [];
        awarenessTick.value += 1;
        return;
      }
      if (payload.type === "awareness_update" && typeof payload.awareness_update_base64 === "string") {
        try {
          awarenessProtocol.applyAwarenessUpdate(awareness, fromBase64(payload.awareness_update_base64), "remote");
          awarenessTick.value += 1;
        } catch {
          /* ignore */
        }
        return;
      }
      if (payload.type === "awareness_remove" && typeof payload.awareness_client_id === "number") {
        awarenessProtocol.removeAwarenessStates(awareness, [payload.awareness_client_id], "remote");
        awarenessTick.value += 1;
        return;
      }
      if (payload.type === "content_saved") {
        syncStatus.value = "synced";
        if (payload.updated_at) {
          lastSavedAt.value = new Date(payload.updated_at).toLocaleTimeString();
        }
        return;
      }
      if (payload.type === "content_sync") {
        let appliedYjs = false;
        if (typeof payload.content_yjs_base64 === "string") {
          try {
            Y.applyUpdate(ydoc, fromBase64(payload.content_yjs_base64), "remote");
            appliedYjs = true;
            syncStatus.value = "synced";
          } catch {
            syncStatus.value = "offline";
          }
        }
        if (!appliedYjs && typeof payload.content_html === "string") {
          content.value = payload.content_html;
          editorEpoch.value += 1;
        }
        finishInitialSync();
        return;
      }
      if (payload.type === "yjs_update" && typeof payload.yjs_update_base64 === "string") {
        try {
          Y.applyUpdate(ydoc, fromBase64(payload.yjs_update_base64), "remote");
          syncStatus.value = "synced";
          if (payload.updated_at) {
            lastSavedAt.value = new Date(payload.updated_at).toLocaleTimeString();
          }
        } catch {
          syncStatus.value = "offline";
        }
        return;
      }
      if (payload.type === "content_update") {
        if (typeof payload.content_html !== "string") {
          return;
        }
        content.value = payload.content_html;
        if (payload.updated_at) {
          lastSavedAt.value = new Date(payload.updated_at).toLocaleTimeString();
        }
      }
    } catch {
      wsStatus.value = "offline";
    }
  };
}

function bindYjsUpdates() {
  if (yjsUpdateHandler) ydoc.off("update", yjsUpdateHandler);
  yjsUpdateHandler = (update, origin) => {
    if (origin === "remote") return;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (debounceTimer) clearTimeout(debounceTimer);
    syncStatus.value = "syncing";
    debounceTimer = setTimeout(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        return;
      }
      const shouldSnapshot = Date.now() - lastSnapshotSentAt >= 2000;
      ws.send(
        JSON.stringify({
          type: "yjs_update",
          note_id: noteId,
          yjs_update_base64: toBase64(update),
          content_yjs_base64: shouldSnapshot ? toBase64(Y.encodeStateAsUpdate(ydoc)) : undefined,
          content_html: editorRef.value?.getHTML?.() || content.value
        })
      );
      if (shouldSnapshot) {
        lastSnapshotSentAt = Date.now();
      }
    }, 600);
  };
  ydoc.on("update", yjsUpdateHandler);
}

function bindAwarenessUpdates() {
  if (awarenessUpdateHandler) awareness.off("update", awarenessUpdateHandler);
  awarenessUpdateHandler = ({ added, updated, removed }, origin) => {
    awarenessTick.value += 1;
    if (origin === "remote") {
      return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return;
    }
    const changed = [...added, ...updated, ...removed];
    if (!changed.length) {
      return;
    }
    const upd = awarenessProtocol.encodeAwarenessUpdate(awareness, changed);
    ws.send(
      JSON.stringify({
        type: "awareness_update",
        note_id: noteId,
        awareness_client_id: awareness.clientID,
        awareness_update_base64: toBase64(upd)
      })
    );
  };
  awareness.on("update", awarenessUpdateHandler);
}

function flushAutosave() {
  return new Promise((resolve) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      resolve();
      return;
    }
    const snapshot = Y.encodeStateAsUpdate(ydoc);
    ws.send(
      JSON.stringify({
        type: "yjs_update",
        note_id: noteId,
        yjs_update_base64: toBase64(snapshot),
        content_yjs_base64: toBase64(snapshot),
        content_html: editorRef.value?.getHTML?.() || content.value
      })
    );
    setTimeout(resolve, 350);
  });
}

function toBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function fromBase64(val) {
  const binary = atob(val);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function colorFromId(id) {
  const palette = ["#3b82f6", "#8b5cf6", "#f59e0b", "#0ea5e9", "#ef4444", "#6366f1", "#10b981"];
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  return palette[hash % palette.length];
}

async function loadEngagement() {
  try {
    comments.value = [];
    rating.rating_avg = 0;
    rating.rating_count = 0;
    rating.my_score = null;
    if (!note.is_published) return;
    const [commentsData, ratingData] = await Promise.all([api.noteComments(noteId), api.noteRating(noteId)]);
    comments.value = commentsData;
    rating.rating_avg = ratingData.rating_avg;
    rating.rating_count = ratingData.rating_count;
    rating.my_score = ratingData.my_score;
  } catch { /* non-critical, silently fail */ }
}

async function loadRevisions() {
  try {
    revisions.value = await api.noteRevisions(noteId);
  } catch { revisions.value = []; }
}

async function createRevision() {
  error.value = "";
  message.value = "";
  try {
    await flushAutosave();
    await api.createRevision(noteId);
    await loadRevisions();
    message.value = "Контрольная точка сохранена";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка сохранения контрольной точки";
  }
}

async function restoreRevision(revisionId) {
  error.value = "";
  message.value = "";
  try {
    const updated = await api.restoreRevision(noteId, revisionId);
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    resetCollaborationDoc(updated.content_html || "");
    fill(updated);
    connectSocket();
    await waitInitialSync();
    editorReady.value = true;
    bindYjsUpdates();
    bindAwarenessUpdates();
    await loadRevisions();
    message.value = "Контрольная точка восстановлена";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка восстановления";
  }
}

async function deleteRevision(revisionId) {
  if (!window.confirm("Удалить выбранную версию безвозвратно?")) return;
  error.value = "";
  message.value = "";
  try {
    await api.deleteRevision(noteId, revisionId);
    await loadRevisions();
    message.value = "Контрольная точка удалена";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка удаления";
  }
}

function formatDate(val) {
  return new Date(val).toLocaleString();
}

async function setRating(score) {
  error.value = "";
  message.value = "";
  try {
    const data = await api.rateNote(noteId, score);
    rating.rating_avg = data.rating_avg;
    rating.rating_count = data.rating_count;
    rating.my_score = data.my_score;
    message.value = "Оценка сохранена";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка оценки";
  }
}

async function sendComment() {
  if (!commentText.value.trim()) return;
  commentLoading.value = true;
  error.value = "";
  message.value = "";
  try {
    const data = await api.addNoteComment(noteId, { content: commentText.value });
    comments.value.push(data);
    commentText.value = "";
    message.value = "Комментарий добавлен";
    clearMsg();
  } catch (err) {
    error.value = err.message || "Ошибка комментария";
  } finally {
    commentLoading.value = false;
  }
}

onMounted(load);

onBeforeUnmount(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }
  if (yjsUpdateHandler) {
    ydoc.off("update", yjsUpdateHandler);
  }
  if (awarenessUpdateHandler) {
    awareness.off("update", awarenessUpdateHandler);
  }
  awareness.setLocalState(null);
  awareness.destroy();
  ydoc.destroy();
  if (ws) {
    ws.onclose = null;
    ws.close();
  }
});
</script>

<style scoped>
.loading-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
}

.error-card {
  text-align: center;
  padding: 40px;
  max-width: 480px;
}

.error-card h2 {
  margin: 0 0 8px;
}

.error-card p {
  margin: 0 0 20px;
}

.note-page {
  display: grid;
  gap: 16px;
}

.note-header {
  padding: 20px 24px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.header-info h1 {
  margin: 0 0 8px;
  font-size: 22px;
}

.header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.presence-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.presence-label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

.presence-user {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
}

.presence-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.tabs-row {
  display: flex;
  gap: 2px;
  padding: 4px;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border-radius: var(--radius-xs);
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: var(--shadow-xs);
}

.tab-panel {
  padding: 24px;
  animation: fade-up 0.3s ease;
}

.meta-grid {
  display: grid;
  gap: 16px;
  max-width: 600px;
}

.field {
  display: grid;
  gap: 6px;
}

.field-full {
  max-width: 100%;
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

.outline-row {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.outline-row input { flex: 1; }

.engage-grid {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
}

.rating-section h3,
.comments-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.rating-display {
  margin-bottom: 12px;
}

.rating-big {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--warn-500), var(--danger-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
}

.rating-count {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
}

.stars {
  display: flex;
  gap: 4px;
}

.star {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: var(--radius-xs);
  background: var(--surface-muted);
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.star:hover {
  background: var(--warn-100);
  color: var(--warn-500);
}

.star.active {
  color: var(--warn-500);
  background: var(--warn-100);
}

.comment-form {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.comments-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.comment-item {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.comment-author {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.comment-body {
  font-size: 14px;
  line-height: 1.5;
}

.editor-panel {
  display: grid;
  gap: 10px;
}

.live-editors {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.live-editor-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: color-mix(in srgb, var(--chip-color) 18%, white);
  border: 1px solid color-mix(in srgb, var(--chip-color) 40%, transparent);
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
}

.history-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.meta-actions {
  margin-bottom: 12px;
}

.revision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.revision-header h3 { margin: 0; }

.revision-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.revision-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.revision-item:hover { background: var(--surface-muted); }

.revision-date {
  font-size: 14px;
  color: var(--text-secondary);
}

.revision-actions {
  display: flex;
  gap: 6px;
}

@media (max-width: 768px) {
  .header-top { flex-direction: column; }
  .engage-grid { grid-template-columns: 1fr; }
  .tabs-row { overflow-x: auto; }
}
</style>
