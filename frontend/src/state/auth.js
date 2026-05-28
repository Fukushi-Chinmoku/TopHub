import { reactive } from "vue";
import { api } from "../api/client";

const state = reactive({
  user: null,
  isReady: false
});

async function initAuth() {
  if (state.isReady) return state.user;
  try {
    const data = await api.me();
    state.user = data.user;
  } catch {
    state.user = null;
  } finally {
    state.isReady = true;
  }
  return state.user;
}

async function login(payload) {
  const data = await api.login(payload);
  state.user = data.user;
  state.isReady = true;
  return data.user;
}

async function register(payload) {
  const data = await api.register(payload);
  state.user = data.user;
  state.isReady = true;
  return data.user;
}

async function logout() {
  try {
    await api.logout();
  } finally {
    state.user = null;
    state.isReady = true;
  }
}

export function useAuth() {
  return { state, initAuth, login, register, logout };
}
