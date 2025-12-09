<template>
  <el-card class="filter-panel" shadow="never">
    <template #header>
      <div class="filter-header">
        <el-icon><Filter /></el-icon>
        <span class="filter-title">筛选条件</span>
        <el-button text @click="handleClearFilters" :disabled="!hasActiveFilters">
          清空
        </el-button>
      </div>
    </template>

    <el-form label-position="top" label-width="80px">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="新闻源">
            <el-select
              v-model="localFilters.source"
              placeholder="选择新闻源"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="source in sources"
                :key="source.source_key"
                :label="source.display_name"
                :value="source.source_key"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="分类">
            <el-select
              v-model="localFilters.category"
              placeholder="选择分类"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="cat in categories"
                :key="cat.value"
                :label="cat.label"
                :value="cat.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="localFilters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleFilterChange"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row v-if="hasActiveFilters" class="active-filters">
        <el-col :span="24">
          <div class="active-filters-label">已应用的筛选：</div>
          <el-tag
            v-if="localFilters.source"
            closable
            @close="clearFilter('source')"
            class="filter-tag"
          >
            新闻源: {{ getSourceName(localFilters.source) }}
          </el-tag>
          <el-tag
            v-if="localFilters.category"
            closable
            @close="clearFilter('category')"
            class="filter-tag"
          >
            分类: {{ getCategoryName(localFilters.category) }}
          </el-tag>
          <el-tag
            v-if="localFilters.dateRange && localFilters.dateRange.length === 2"
            closable
            @close="clearFilter('dateRange')"
            class="filter-tag"
          >
            日期: {{ localFilters.dateRange[0] }} ~ {{ localFilters.dateRange[1] }}
          </el-tag>
        </el-col>
      </el-row>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Filter } from '@element-plus/icons-vue'
import { useFiltersStore } from '../../store/filters'
import articleService from '../../services/articleService'

const emit = defineEmits(['filter-change'])

const filtersStore = useFiltersStore()
const sources = ref([])
const categories = ref([
  { label: '娱乐', value: 'ent' },
  { label: '国内', value: 'china' },
  { label: '国际', value: 'world' },
  { label: '军事', value: 'military' },
  { label: '财经', value: 'finance' },
  { label: '科技', value: 'tech' },
  { label: '体育', value: 'sports' }
])

const localFilters = ref({
  source: null,
  category: null,
  dateRange: []
})

const hasActiveFilters = computed(() => {
  return (
    localFilters.value.source ||
    localFilters.value.category ||
    (localFilters.value.dateRange && localFilters.value.dateRange.length === 2)
  )
})

onMounted(async () => {
  try {
    const response = await articleService.getSources(true)
    sources.value = response.sources
  } catch (error) {
    console.error('Failed to fetch sources:', error)
  }

  // Load saved filters from store
  localFilters.value.source = filtersStore.selectedSource
  localFilters.value.category = filtersStore.selectedCategory
  localFilters.value.dateRange = filtersStore.dateRange
})

function handleFilterChange() {
  // Update store
  filtersStore.setSource(localFilters.value.source)
  filtersStore.setCategory(localFilters.value.category)
  filtersStore.setDateRange(localFilters.value.dateRange)

  // Build params
  const params = {}
  if (localFilters.value.source) {
    params.source = localFilters.value.source
  }
  if (localFilters.value.category) {
    params.category = localFilters.value.category
  }
  if (localFilters.value.dateRange && localFilters.value.dateRange.length === 2) {
    params.startDate = localFilters.value.dateRange[0]
    params.endDate = localFilters.value.dateRange[1]
  }

  emit('filter-change', params)
}

function handleClearFilters() {
  localFilters.value = {
    source: null,
    category: null,
    dateRange: []
  }
  filtersStore.clearFilters()
  emit('filter-change', {})
}

function clearFilter(filterType) {
  localFilters.value[filterType] = filterType === 'dateRange' ? [] : null
  handleFilterChange()
}

function getSourceName(sourceKey) {
  const source = sources.value.find((s) => s.source_key === sourceKey)
  return source ? source.display_name : sourceKey
}

function getCategoryName(categoryValue) {
  const category = categories.value.find((c) => c.value === categoryValue)
  return category ? category.label : categoryValue
}
</script>

<style scoped>
.filter-panel {
  margin-bottom: 1.5rem;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-title {
  flex: 1;
  font-weight: 600;
  font-size: 1rem;
}

.el-select,
.el-date-picker {
  width: 100%;
}

.active-filters {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ebeef5;
}

.active-filters-label {
  font-size: 0.875rem;
  color: #606266;
  margin-bottom: 0.5rem;
}

.filter-tag {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
