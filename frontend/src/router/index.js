import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../state/auth";
import CabinetView from "../views/CabinetView.vue";
import FriendsView from "../views/FriendsView.vue";
import GroupsView from "../views/GroupsView.vue";
import LoginView from "../views/LoginView.vue";
import NoteDetailView from "../views/NoteDetailView.vue";
import NoteWizardView from "../views/NoteWizardView.vue";
import UserNotesView from "../views/UserNotesView.vue";
import PublicNotesView from "../views/PublicNotesView.vue";
import NotFoundView from "../views/NotFoundView.vue";

const routes = [
  { path: "/", redirect: "/explore" },
  { path: "/login", component: LoginView, meta: { guestOnly: true } },
  { path: "/explore", component: PublicNotesView, meta: { requiresAuth: true } },
  { path: "/cabinet", component: CabinetView, meta: { requiresAuth: true } },
  { path: "/groups", component: GroupsView, meta: { requiresAuth: true } },
  { path: "/friends", component: FriendsView, meta: { requiresAuth: true } },
  { path: "/notes/new", component: NoteWizardView, meta: { requiresAuth: true } },
  { path: "/notes/:id", component: NoteDetailView, meta: { requiresAuth: true } },
  { path: "/users/:login", component: UserNotesView, meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", component: NotFoundView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  const auth = useAuth();
  await auth.initAuth();
  const isAuthenticated = Boolean(auth.state.user);

  if (to.meta.requiresAuth && !isAuthenticated) return "/login";
  if (to.meta.guestOnly && isAuthenticated) return "/explore";
  return true;
});

export default router;
