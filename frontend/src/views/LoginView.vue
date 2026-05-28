<template>
  <section class="login-page">
    <div class="login-card card animate-scale-in">
      <div class="login-header">
        <div class="login-logo">Co</div>
        <h1>Top Academy</h1>
        <p>Платформа совместных конспектов</p>
      </div>

      <div class="tabs">
        <button :class="['tab', { active: mode === 'login' }]" @click="switchMode('login')">Вход</button>
        <button :class="['tab', { active: mode === 'register' }]" @click="switchMode('register')">Регистрация</button>
      </div>

      <form class="form" @submit.prevent="submit">
        <div class="field">
          <label for="login">Логин</label>
          <input
            id="login"
            v-model.trim="login"
            required
            minlength="3"
            maxlength="32"
            placeholder="Только латиница, 3–32 символа"
            autocomplete="username"
          />
        </div>

        <div v-if="mode === 'register'" class="field animate-fade-in">
          <label for="displayName">Отображаемое имя</label>
          <input
            id="displayName"
            v-model.trim="displayName"
            required
            minlength="2"
            maxlength="64"
            placeholder="Ваше имя"
            autocomplete="name"
          />
        </div>

        <div class="field">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            minlength="8"
            maxlength="128"
            placeholder="Минимум 8 символов"
            autocomplete="current-password"
          />
        </div>

        <button class="btn btn-primary submit-btn" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>{{ mode === 'login' ? 'Войти в аккаунт' : 'Создать аккаунт' }}</span>
        </button>

        <p v-if="error" class="text-danger error-msg animate-fade-in">{{ error }}</p>
      </form>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../state/auth";

const auth = useAuth();
const router = useRouter();

const mode = ref("login");
const login = ref("");
const displayName = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

function switchMode(newMode) {
  mode.value = newMode;
  error.value = "";
}

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    if (mode.value === "login") {
      await auth.login({ login: login.value, password: password.value });
    } else {
      await auth.register({
        login: login.value,
        password: password.value,
        display_name: displayName.value
      });
      await auth.login({ login: login.value, password: password.value });
    }
    await router.push("/explore");
  } catch (err) {
    error.value = err.message || "Ошибка авторизации";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 36px 32px;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-logo {
  width: 52px;
  height: 52px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: white;
  font-weight: 800;
  font-size: 24px;
  box-shadow: var(--shadow-brand);
}

.login-header h1 {
  margin: 0;
  font-size: 28px;
}

.login-header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  margin-bottom: 24px;
}

.tab {
  flex: 1;
  padding: 8px;
  border-radius: var(--radius-xs);
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: var(--shadow-xs);
}

.form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.submit-btn {
  min-height: 44px;
  font-size: 15px;
  margin-top: 4px;
}

.error-msg {
  margin: 0;
  text-align: center;
}
</style>
