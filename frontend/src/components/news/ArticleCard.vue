<template>
  <el-card class="article-card" shadow="hover">
    <div class="article-content">
      <h3 class="article-title">
        <a :href="article.url" target="_blank" rel="noopener noreferrer">
          {{ article.title }}
        </a>
      </h3>
      <div class="article-meta">
        <el-tag size="small" type="info">{{ article.source_key }}</el-tag>
        <el-tag v-if="article.category" size="small">{{ article.category }}</el-tag>
        <span class="article-time">{{ formatTime(article.published_at) }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  article: {
    type: Object,
    required: true
  }
})

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000 / 60) // minutes

  if (diff < 60) {
    return `${diff}分钟前`
  } else if (diff < 1440) {
    return `${Math.floor(diff / 60)}小时前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped>
.article-card {
  margin-bottom: 1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.article-card:hover {
  transform: translateY(-2px);
}

.article-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.article-title {
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
}

.article-title a {
  color: #333;
  text-decoration: none;
  transition: color 0.2s;
}

.article-title a:hover {
  color: #667eea;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.article-time {
  margin-left: auto;
}
</style>
