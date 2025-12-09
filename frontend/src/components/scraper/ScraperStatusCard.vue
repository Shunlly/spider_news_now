<template>
  <el-card class="scraper-status-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="source-name">{{ scraper.source_name }}</span>
        <el-tag :type="statusTagType" size="small">
          {{ statusText }}
        </el-tag>
      </div>
    </template>

    <div class="card-content">
      <!-- Current Status -->
      <div class="status-section">
        <div class="info-row">
          <span class="label">状态:</span>
          <span class="value">{{ enabledText }}</span>
        </div>
        <div class="info-row">
          <span class="label">失败次数:</span>
          <span class="value" :class="{ error: scraper.failure_count > 0 }">
            {{ scraper.failure_count }}
          </span>
        </div>
      </div>

      <!-- Last Run Info -->
      <div v-if="scraper.last_run" class="run-section">
        <div class="section-title">最近运行</div>
        <div class="info-row">
          <span class="label">时间:</span>
          <span class="value">{{ formatDateTime(scraper.last_run.started_at) }}</span>
        </div>
        <div class="info-row">
          <span class="label">耗时:</span>
          <span class="value">{{ scraper.last_run.duration_seconds }}秒</span>
        </div>
        <div class="info-row">
          <span class="label">抓取:</span>
          <span class="value">
            {{ scraper.last_run.articles_scraped }}篇
            (新增 {{ scraper.last_run.articles_new }})
          </span>
        </div>
      </div>

      <!-- Current Run Info -->
      <div v-if="scraper.current_run" class="run-section current">
        <div class="section-title">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在运行</span>
        </div>
        <div class="info-row">
          <span class="label">开始时间:</span>
          <span class="value">{{ formatDateTime(scraper.current_run.started_at) }}</span>
        </div>
        <div class="info-row">
          <span class="label">已抓取:</span>
          <span class="value">{{ scraper.current_run.articles_scraped }}篇</span>
        </div>
      </div>

      <!-- Next Run -->
      <div v-if="scraper.next_run_at && scraper.enabled" class="info-row next-run">
        <span class="label">下次运行:</span>
        <span class="value">{{ formatDateTime(scraper.next_run_at) }}</span>
      </div>

      <!-- Actions -->
      <div class="actions">
        <el-button
          type="primary"
          size="small"
          :disabled="scraper.current_run !== null || !scraper.enabled"
          :loading="triggering"
          @click="handleTrigger"
        >
          立即运行
        </el-button>
        <el-button
          type="default"
          size="small"
          @click="handleViewHistory"
        >
          查看历史
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import scraperService from '../../services/scraperService'

const props = defineProps({
  scraper: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh', 'view-history'])

const triggering = ref(false)

const statusTagType = computed(() => {
  if (props.scraper.current_run) return 'warning'
  if (!props.scraper.enabled) return 'info'
  if (props.scraper.failure_count > 3) return 'danger'
  if (props.scraper.failure_count > 0) return 'warning'
  return 'success'
})

const statusText = computed(() => {
  if (props.scraper.current_run) return '运行中'
  if (!props.scraper.enabled) return '已禁用'
  if (props.scraper.status === 'failed') return '失败'
  if (props.scraper.status === 'idle') return '空闲'
  return props.scraper.status
})

const enabledText = computed(() => {
  return props.scraper.enabled ? '已启用' : '已禁用'
})

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function handleTrigger() {
  try {
    triggering.value = true
    await scraperService.triggerScraper(props.scraper.source_key)
    ElMessage.success(`已触发 ${props.scraper.source_name} 爬虫`)
    emit('refresh')
  } catch (error) {
    ElMessage.error('触发失败：' + error.message)
  } finally {
    triggering.value = false
  }
}

function handleViewHistory() {
  emit('view-history', props.scraper.source_key)
}
</script>

<style scoped>
.scraper-status-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.source-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-section,
.run-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.run-section {
  padding: 0.75rem;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.run-section.current {
  background-color: #fff7e6;
  border: 1px solid #ffd666;
}

.section-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
}

.info-row .label {
  color: #909399;
}

.info-row .value {
  font-weight: 500;
  color: #303133;
}

.info-row .value.error {
  color: #f56c6c;
}

.info-row.next-run {
  padding-top: 0.5rem;
  border-top: 1px solid #ebeef5;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.actions .el-button {
  flex: 1;
}
</style>
