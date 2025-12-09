<template>
  <header class="app-header">
    <div class="container">
      <h1 class="title">📰 新闻聚合系统</h1>
      <nav class="nav">
        <router-link to="/" class="nav-link">新闻列表</router-link>
        <router-link to="/dashboard" class="nav-link">监控面板</router-link>
      </nav>
    </div>
  </header>
</template>

<script setup>
// Header component
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>
