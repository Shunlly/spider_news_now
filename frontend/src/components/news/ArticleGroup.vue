<template>
  <div class="article-group">
    <div class="group-header">
      <h2 class="group-title">{{ group.source_name }}</h2>
      <el-tag type="info">{{ group.article_count }} 篇文章</el-tag>
    </div>
    <div class="articles-list">
      <ArticleCard v-for="article in group.articles" :key="article.id" :article="article" />
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import ArticleCard from './ArticleCard.vue'

defineProps({
  group: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.article-group {
  margin-bottom: 2rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.group-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

.articles-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
