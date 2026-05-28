const API_BASE = "/api";

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

function normalizeErrorDetail(detail) {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") return "";
        const location = Array.isArray(item.loc) ? item.loc.join(".") : "";
        const message = typeof item.msg === "string" ? item.msg : "";
        if (!location && !message) return "";
        if (!location) return message;
        if (!message) return location;
        return `${location}: ${message}`;
      })
      .filter(Boolean);
    if (messages.length) return messages.join("; ");
  }
  return "Произошла ошибка";
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });
  } catch {
    throw new Error("Нет соединения с сервером. Проверьте интернет-подключение.");
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(normalizeErrorDetail(data?.detail));
  }
  return data;
}

export const api = {
  register(payload) {
    return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
  },
  login(payload) {
    return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
  },
  logout() {
    return request("/auth/logout", { method: "POST" });
  },
  me() {
    return request("/auth/me");
  },
  subjects() {
    return request("/subjects");
  },
  cabinet(params = {}) {
    return request(`/cabinet${buildQuery(params)}`);
  },
  createNote(payload) {
    return request("/notes", { method: "POST", body: JSON.stringify(payload) });
  },
  note(noteId) {
    return request(`/notes/${noteId}`);
  },
  updateNote(noteId, payload) {
    return request(`/notes/${noteId}`, { method: "PATCH", body: JSON.stringify(payload) });
  },
  publishNote(noteId) {
    return request(`/notes/${noteId}/publish`, { method: "POST" });
  },
  noteRevisions(noteId) {
    return request(`/notes/${noteId}/revisions`);
  },
  createRevision(noteId) {
    return request(`/notes/${noteId}/revisions`, { method: "POST" });
  },
  restoreRevision(noteId, revisionId) {
    return request(`/notes/${noteId}/revisions/${revisionId}/restore`, { method: "POST" });
  },
  deleteRevision(noteId, revisionId) {
    return request(`/notes/${noteId}/revisions/${revisionId}`, { method: "DELETE" });
  },
  noteComments(noteId) {
    return request(`/notes/${noteId}/comments`);
  },
  addNoteComment(noteId, payload) {
    return request(`/notes/${noteId}/comments`, { method: "POST", body: JSON.stringify(payload) });
  },
  noteRating(noteId) {
    return request(`/notes/${noteId}/rating`);
  },
  rateNote(noteId, score) {
    return request(`/notes/${noteId}/rating`, { method: "PUT", body: JSON.stringify({ score }) });
  },
  myGroups() {
    return request("/groups/mine");
  },
  createGroup(payload) {
    return request("/groups", { method: "POST", body: JSON.stringify(payload) });
  },
  joinGroup(payload) {
    return request("/groups/join-request", { method: "POST", body: JSON.stringify(payload) });
  },
  groupMembers(groupId) {
    return request(`/groups/${groupId}/members`);
  },
  groupJoinRequests(groupId) {
    return request(`/groups/${groupId}/requests/incoming`);
  },
  respondGroupJoinRequest(groupId, userId, action) {
    return request(`/groups/${groupId}/requests/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ action })
    });
  },
  groupNotes(groupId, params = {}) {
    return request(`/groups/${groupId}/notes${buildQuery(params)}`);
  },
  leaveGroup(groupId) {
    return request(`/groups/${groupId}/leave`, { method: "POST" });
  },
  deleteGroup(groupId) {
    return request(`/groups/${groupId}`, { method: "DELETE" });
  },
  publicNotes(params = {}) {
    return request(`/notes/public${buildQuery(params)}`);
  },
  deleteNote(noteId) {
    return request(`/notes/${noteId}`, { method: "DELETE" });
  },
  sendFriendRequest(payload) {
    return request("/friends/request", { method: "POST", body: JSON.stringify(payload) });
  },
  incomingFriendRequests() {
    return request("/friends/requests/incoming");
  },
  respondFriendRequest(requestId, action) {
    return request(`/friends/requests/${requestId}`, {
      method: "PATCH",
      body: JSON.stringify({ action })
    });
  },
  friends() {
    return request("/friends");
  },
  removeFriend(userId) {
    return request(`/friends/${userId}`, { method: "DELETE" });
  },
  userNotes(login, params = {}) {
    return request(`/users/${login}/notes${buildQuery(params)}`);
  }
};
