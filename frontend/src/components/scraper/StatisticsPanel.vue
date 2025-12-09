<template>
  <el-card class="statistics-panel" shadow="hover">
    <template #header>
      <div class="panel-header">
        <el-icon><DataAnalysis /></el-icon>
        <span class="panel-title">系统统计</span>
      </div>
    </template>

    <div v-loading="loading" class="statistics-content">
      <div v-if="statistics" class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ statistics.total_scrapers }}</div>
          <div class="stat-label">爬虫总数</div>
        </div>
        <div class="stat-item success">
          <div class="stat-value">{{ statistics.active_runs }}</div>
          <div class="stat-label">运行中</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ enabledScrapers }}</div>
          <div class="stat-label">已启用</div>
        </div>
        <div class="stat-item danger">
          <div class="stat-value">{{ failedScrapers }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>

      <el-divider />

      <div v-if="newsStats" class="stats-grid">
        <div class="stat-item primary">
          <div class="stat-value">{{ newsStats.total_articles }}</div>
          <div class="stat-label">新闻总数</div>
        </div>
        <div class="stat-item success">
          <div class="stat-value">{{ newsStats.articles_today }}</div>
          <div class="stat-label">今日新增</div>
        </div>
        <div class="stat-item warning">
          <div class="stat-value">{{ newsStats.articles_week }}</div>
          <div class="stat-label">本周新增</div>
        </div>
        <div class="stat-item info">
          <div class="stat-value">{{ newsStats.total_sources }}</div>
          <div class="stat-label">新闻源</div>
        </div>
      </div>

      <div class="refresh-info">
        <span class="last-update">
          最后更新: {{ lastUpdateTime }}
        </span>
        <el-button text @click="refresh" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'
import articleService from '../../services/articleService'

const props = defineProps({
  scrapers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh'])

const loading = ref(false)
const newsStats = ref(null)
const lastUpdateTime = ref('-')

const statistics = computed(() => {
  if (!props.scrapers || props.scrapers.length === 0) return null

  return {
    total_scrapers: props.scrapers.length,
    active_runs: props.scrapers.filter((s) => s.current_run !== null).length
  }
})

const enabledScrapers = computed(() => {
  return props.scrapers.filter((s) => s.enabled).length
})

const failedScrapers = computed(() => {
  return props.scrapers.filter((s) => s.failure_count > 0).length
})

onMounted(async () => {
  await loadNewsStatistics()
})

async function loadNewsStatistics() {
  try {
    loading.value = true
    const response = await articleService.getStatistics()
    newsStats.value = response
    updateLastUpdateTime()
  } catch (error) {
    console.error('Failed to load news statistics:', error)
  } finally {
    loading.value = false
  }
}

function updateLastUpdateTime() {
  const now = new Date()
  lastUpdateTime.value = now.toLocaleTimeString('zh-CN')
}

async function refresh() {
  await loadNewsStatistics()
  emit('refresh')
}
</script>

<style scoped>
.statistics-panel {
  margin-bottom: 1.5rem;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
}

.statistics-content {
  min-height: 150px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f5f7fa;
  transition: transform 0.2s;
}

.stat-item:hover {
  transform: translateY(-2px);
}

.stat-item.primary {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
}

.stat-item.success {
  background-color: #f0f9ff;
  border: 1px solid #d1eeff;
}

.stat-item.warning {
  background-color: #fef7ec;
  border: 1px solid #faecd8;
}

.stat-item.danger {
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
}

.stat-item.info {
  background-color: #f4f4f5;
  border: 1px solid #e4e7ed;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #303133;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #909399;
}

.refresh-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #ebeef5;
}

.last-update {
  font-size: 0.75rem;
  color: #909399;
}
</style>
