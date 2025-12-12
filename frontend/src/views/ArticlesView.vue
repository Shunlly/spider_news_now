<template>
  <DefaultLayout>
    <div class="articles-view">
      <el-alert v-if="articlesStore.error" type="error" :closable="false" class="error-alert">
        {{ articlesStore.error }}
      </el-alert>

      <!-- Filter Panel -->
      <FilterPanel @filter-change="handleFilterChange" />

      <div v-loading="articlesStore.loading" class="content">
        <!-- List view when source is selected -->
        <template v-if="isListMode">
          <div v-if="articlesStore.hasArticles" class="articles-list-container">
            <div class="list-header">
              <span>共 {{ articlesStore.pagination.total }} 篇文章</span>
            </div>
            <div class="articles-list">
              <ArticleCard
                v-for="article in articlesStore.articles"
                :key="article.id"
                :article="article"
              />
            </div>
            <!-- Pagination -->
            <el-pagination
              v-if="articlesStore.pagination.totalPages > 1"
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="articlesStore.pagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              class="pagination"
              @current-change="handlePageChange"
              @size-change="handlePageSizeChange"
            />
          </div>
          <el-empty v-else-if="!articlesStore.loading" description="暂无新闻数据">
            <el-button type="primary" @click="loadArticles">刷新</el-button>
          </el-empty>
        </template>

        <!-- Grouped view (default) -->
        <template v-else>
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
        </template>
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
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useArticlesStore } from '../store/articles'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ArticleGroup from '../components/news/ArticleGroup.vue'
import ArticleCard from '../components/news/ArticleCard.vue'
import FilterPanel from '../components/news/FilterPanel.vue'

const articlesStore = useArticlesStore()
const currentFilters = ref({})
const currentPage = ref(1)
const pageSize = ref(50)

// Use list mode when a specific source is selected
const isListMode = computed(() => !!currentFilters.value.source)

async function loadArticles() {
  try {
    if (isListMode.value) {
      // Fetch paginated list when source is selected
      await articlesStore.fetchArticles({
        source: currentFilters.value.source,
        category: currentFilters.value.category,
        startDate: currentFilters.value.startDate,
        endDate: currentFilters.value.endDate,
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } else {
      // Fetch grouped articles by default
      await articlesStore.fetchGroupedArticles({
        category: currentFilters.value.category,
        startDate: currentFilters.value.startDate,
        limitPerSource: 10
      })
    }
    ElMessage.success('新闻加载成功')
  } catch (error) {
    ElMessage.error('加载新闻失败：' + error.message)
  }
}

function handleFilterChange(filters) {
  currentFilters.value = filters
  currentPage.value = 1 // Reset to first page when filters change
  loadArticles()
}

function handlePageChange(page) {
  currentPage.value = page
  loadArticles()
}

function handlePageSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadArticles()
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

.articles-list-container {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.list-header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
  font-size: 0.9rem;
}

.articles-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pagination {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.refresh-button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 100;
}
</style>
