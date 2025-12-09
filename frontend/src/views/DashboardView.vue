<template>
  <DefaultLayout>
    <div class="dashboard-view">
      <div class="dashboard-header">
        <h2>爬虫监控面板</h2>
        <el-button
          type="primary"
          :icon="Refresh"
          :loading="loading"
          @click="loadData"
        >
          刷新
        </el-button>
      </div>

      <el-alert v-if="error" type="error" :closable="false" class="error-alert">
        {{ error }}
      </el-alert>

      <!-- Statistics Panel -->
      <StatisticsPanel :scrapers="scrapers" @refresh="loadData" />

      <!-- Scraper Status Cards -->
      <div v-loading="loading" class="scrapers-grid">
        <ScraperStatusCard
          v-for="scraper in scrapers"
          :key="scraper.source_key"
          :scraper="scraper"
          @refresh="loadData"
          @view-history="handleViewHistory"
        />
      </div>

      <!-- Run History Dialog -->
      <el-dialog
        v-model="historyDialogVisible"
        :title="`${currentSourceName} - 运行历史`"
        width="80%"
        destroy-on-close
      >
        <div v-loading="historyLoading" class="history-content">
          <el-table :data="runs" stripe>
            <el-table-column prop="started_at" label="开始时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.started_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="duration_seconds" label="耗时" width="100">
              <template #default="{ row }">
                {{ row.duration_seconds }}秒
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="articles_scraped" label="抓取数量" width="120" />
            <el-table-column prop="articles_new" label="新增" width="100" />
            <el-table-column prop="articles_duplicate" label="重复" width="100" />
            <el-table-column prop="error_message" label="错误信息" min-width="200">
              <template #default="{ row }">
                <span v-if="row.error_message" class="error-text">
                  {{ row.error_message }}
                </span>
                <span v-else class="success-text">-</span>
              </template>
            </el-table-column>
          </el-table>

          <!-- Pagination -->
          <el-pagination
            v-if="historyTotal > historyPageSize"
            v-model:current-page="historyPage"
            v-model:page-size="historyPageSize"
            :total="historyTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pagination"
            @current-change="loadHistory"
            @size-change="loadHistory"
          />
        </div>
      </el-dialog>
    </div>
  </DefaultLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ScraperStatusCard from '../components/scraper/ScraperStatusCard.vue'
import StatisticsPanel from '../components/scraper/StatisticsPanel.vue'
import scraperService from '../services/scraperService'

const loading = ref(false)
const error = ref(null)
const scrapers = ref([])

const historyDialogVisible = ref(false)
const historyLoading = ref(false)
const runs = ref([])
const currentSourceKey = ref(null)
const currentSourceName = ref('')
const historyPage = ref(1)
const historyPageSize = ref(20)
const historyTotal = ref(0)

onMounted(() => {
  loadData()

  // Auto refresh every 30 seconds
  setInterval(() => {
    loadData(true)
  }, 30000)
})

async function loadData(silent = false) {
  try {
    if (!silent) loading.value = true
    error.value = null

    const response = await scraperService.getScrapersStatus()
    scrapers.value = response.scrapers || []
  } catch (err) {
    error.value = '加载爬虫状态失败: ' + err.message
    if (!silent) {
      ElMessage.error(error.value)
    }
  } finally {
    loading.value = false
  }
}

async function handleViewHistory(sourceKey) {
  currentSourceKey.value = sourceKey
  const scraper = scrapers.value.find((s) => s.source_key === sourceKey)
  currentSourceName.value = scraper ? scraper.source_name : sourceKey
  historyPage.value = 1
  historyDialogVisible.value = true
  await loadHistory()
}

async function loadHistory() {
  try {
    historyLoading.value = true
    const response = await scraperService.getScraperRuns(currentSourceKey.value, {
      page: historyPage.value,
      pageSize: historyPageSize.value
    })
    runs.value = response.runs || []
    historyTotal.value = response.total || 0
  } catch (err) {
    ElMessage.error('加载运行历史失败: ' + err.message)
  } finally {
    historyLoading.value = false
  }
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getStatusTagType(status) {
  switch (status) {
    case 'success':
      return 'success'
    case 'failed':
      return 'danger'
    case 'timeout':
      return 'warning'
    case 'running':
      return 'primary'
    default:
      return 'info'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'success':
      return '成功'
    case 'failed':
      return '失败'
    case 'timeout':
      return '超时'
    case 'running':
      return '运行中'
    default:
      return status
  }
}
</script>

<style scoped>
.dashboard-view {
  width: 100%;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.error-alert {
  margin-bottom: 1.5rem;
}

.scrapers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.history-content {
  min-height: 300px;
}

.pagination {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
}

.error-text {
  color: #f56c6c;
  font-size: 0.875rem;
}

.success-text {
  color: #67c23a;
}
</style>
