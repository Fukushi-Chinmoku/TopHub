<template>
  <section class="not-found animate-fade-up">
    <div class="nf-code">404</div>
    <h2>Страница не найдена</h2>
    <p>Возможно, она была удалена или указан неверный адрес.</p>
    <RouterLink class="btn btn-primary" to="/cabinet">Вернуться в кабинет</RouterLink>
  </section>
</template>

<script setup>
import { RouterLink } from "vue-router";
</script>

<style scoped>
.not-found {
  text-align: center;
  padding: 80px 24px;
}

.nf-code {
  font-size: 96px;
  font-weight: 800;
  letter-spacing: -0.04em;
  background: linear-gradient(135deg, var(--brand-500), var(--accent-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  margin-bottom: 12px;
}

h2 {
  margin: 0 0 8px;
  font-size: 24px;
}

p {
  margin: 0 0 24px;
  color: var(--text-secondary);
}
</style>
