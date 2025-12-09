<template>
  <DefaultLayout>
    <div class="articles-view">
      <el-alert v-if="articlesStore.error" type="error" :closable="false" class="error-alert">
        {{ articlesStore.error }}
      </el-alert>

      <!-- Filter Panel -->
      <FilterPanel @filter-change="handleFilterChange" />

      <div v-loading="articlesStore.loading" class="content">
        <div v-if="articlesStore.hasGroupedArticles" class="groups-container">
          <ArticleGroup
            v-for="group in articlesStore.groupedArticles"
            :key="group.source_key"
            :group="group"
          />
        </div>

        <el-empty v-else-if="!articlesStore.loading" description="暂无新闻数据">
          <el-button type="primary" @click="loadArticles">刷新</el-button>
        </el-empty>
      </div>

      <div class="refresh-button">
        <el-button
          type="primary"
          :icon="Refresh"
          :loading="articlesStore.loading"
          @click="loadArticles"
        >
          刷新新闻
        </el-button>
      </div>
    </div>
  </DefaultLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useArticlesStore } from '../store/articles'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ArticleGroup from '../components/news/ArticleGroup.vue'
import FilterPanel from '../components/news/FilterPanel.vue'

const articlesStore = useArticlesStore()
const currentFilters = ref({})

async function loadArticles(filters = {}) {
  try {
    await articlesStore.fetchGroupedArticles({
      limitPerSource: 10,
      ...filters
    })
    ElMessage.success('新闻加载成功')
  } catch (error) {
    ElMessage.error('加载新闻失败：' + error.message)
  }
}

function handleFilterChange(filters) {
  currentFilters.value = filters
  loadArticles(filters)
}

onMounted(() => {
  loadArticles()
})
</script>

<style scoped>
.articles-view {
  width: 100%;
}

.error-alert {
  margin-bottom: 1rem;
}

.content {
  min-height: 400px;
}

.groups-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.refresh-button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 100;
}
</style>
