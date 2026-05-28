<template>
  <div class="app-shell">
    <header v-if="auth.state.user" class="app-header">
      <div class="header-inner">
        <RouterLink to="/explore" class="logo">
          <span class="logo-icon">TA</span>
          <span class="logo-text">Top Academy</span>
        </RouterLink>

        <nav class="nav" aria-label="Главная навигация">
          <RouterLink to="/explore" class="nav-link">
            <AppIcon name="notes" :size="18" /> Конспекты
          </RouterLink>
          <RouterLink to="/groups" class="nav-link">
            <AppIcon name="groups" :size="18" /> Группы
          </RouterLink>
          <RouterLink to="/friends" class="nav-link">
            <AppIcon name="friends" :size="18" /> Друзья
          </RouterLink>
        </nav>

        <div class="header-right">
          <RouterLink to="/notes/new" class="btn btn-primary btn-sm new-note-btn">
            <AppIcon name="plus" :size="16" /> Конспект
          </RouterLink>
          <RouterLink to="/cabinet" class="user-pill" title="Личный кабинет">
            <span class="avatar">{{ userInitial }}</span>
            <span class="user-name">{{ auth.state.user.login }}</span>
          </RouterLink>
          <button class="btn btn-ghost btn-sm logout-btn" @click="onLogout">
            <AppIcon name="logout" :size="16" /> Выйти
          </button>
        </div>

        <button class="mobile-menu-btn btn btn-ghost btn-sm" aria-label="Меню" @click="mobileOpen = !mobileOpen">
          <AppIcon name="menu" :size="20" />
        </button>
      </div>

      <nav v-if="mobileOpen" class="mobile-nav animate-fade-in">
        <RouterLink to="/explore" class="nav-link" @click="mobileOpen = false">Конспекты</RouterLink>
        <RouterLink to="/cabinet" class="nav-link" @click="mobileOpen = false">Кабинет</RouterLink>
        <RouterLink to="/groups" class="nav-link" @click="mobileOpen = false">Группы</RouterLink>
        <RouterLink to="/friends" class="nav-link" @click="mobileOpen = false">Друзья</RouterLink>
        <RouterLink to="/notes/new" class="nav-link" @click="mobileOpen = false">+ Новый</RouterLink>
        <button class="btn btn-ghost btn-sm" @click="onLogout">Выйти</button>
      </nav>
    </header>

    <main class="main-content">
      <RouterView v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";
import AppIcon from "./components/icons/AppIcon.vue";
import { useAuth } from "./state/auth";

const auth = useAuth();
const router = useRouter();
const mobileOpen = ref(false);

const userInitial = computed(() => {
  const login = auth.state.user?.login || "";
  return login.charAt(0).toUpperCase();
});

async function onLogout() {
  try {
    await auth.logout();
  } finally {
    mobileOpen.value = false;
    await router.push("/login");
  }
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--border);
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  height: 56px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: white;
  font-weight: 800;
  font-size: 16px;
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.nav {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: 32px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

.nav-link.router-link-active {
  background: var(--brand-50);
  color: var(--brand-700);
}

.header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-note-btn,
.logout-btn {
  min-height: 34px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: var(--radius-full);
  background: var(--surface-muted);
  text-decoration: none;
  transition: background var(--transition-fast);
}

.user-pill:hover {
  background: var(--brand-50);
}

.avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-400), var(--accent-500));
  color: white;
  font-weight: 700;
  font-size: 13px;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.mobile-menu-btn {
  display: none;
  margin-left: auto;
  font-size: 20px;
}

.mobile-nav {
  display: none;
  flex-direction: column;
  gap: 2px;
  padding: 8px 24px 16px;
  border-top: 1px solid var(--border);
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

@media (max-width: 860px) {
  .nav,
  .header-right {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .mobile-nav {
    display: flex;
  }

  .header-inner {
    padding: 0 16px;
  }

  .main-content {
    padding: 16px;
  }
}
</style>
