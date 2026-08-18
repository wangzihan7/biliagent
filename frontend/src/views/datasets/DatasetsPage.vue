<template>
  <div class="space-y-5">
    <section>
      <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-500">数据集列表</span>
            <el-input
              v-model="keyword"
              size="small"
              placeholder="按名称或关键词过滤"
              class="w-52"
              clearable
            >
              <template #prefix>
                <el-icon><i-ep-search /></el-icon>
              </template>
            </el-input>
          </div>
          <el-button size="small" @click="fetchDatasets">刷新</el-button>
        </div>

        <el-table
          v-loading="loadingDatasets"
          :data="datasets"
          border
          size="small"
          class="rounded-xl"
        >
          <el-table-column prop="name" label="数据集名称" min-width="180" />
          <el-table-column prop="keyword" label="关键词" min-width="140" />
          <el-table-column prop="video_count" label="视频数" width="80" />
          <el-table-column prop="comment_count" label="评论数" width="80" />
          <el-table-column prop="danmaku_count" label="弹幕数" width="80" />
          <el-table-column label="创建时间" min-width="160">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleExport(row.dataset_id, 'jsonl')">
                导出 JSONL
              </el-button>
              <el-button type="primary" link size="small" @click="handleExport(row.dataset_id, 'csv')">
                导出 CSV
              </el-button>
              <el-popconfirm
                v-if="auth.isAdmin"
                title="删除该数据集？相关视频/评论/弹幕和向量库会一起清理。"
                confirm-button-text="删除"
                cancel-button-text="取消"
                @confirm="handleDelete(row.dataset_id)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div class="mt-3 flex justify-end">
          <el-pagination
            v-model:current-page="datasetPage"
            v-model:page-size="datasetPageSize"
            background
            layout="prev, pager, next, sizes, total"
            :total="totalDatasets"
            :page-sizes="[10, 20, 50]"
            @current-change="handleDatasetPageChange"
            @size-change="handleDatasetSizeChange"
          />
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { listDatasets, exportDataset, deleteDataset } from '@/api/datasets';
import { useAuthStore } from '@/stores/auth';
import type { DatasetSummary } from '@/types/api';

const auth = useAuthStore();

const datasets = ref<DatasetSummary[]>([]);
const totalDatasets = ref(0);
const loadingDatasets = ref(false);
const keyword = ref('');
const datasetPage = ref(1);
const datasetPageSize = ref(10);

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const fetchDatasets = async () => {
  loadingDatasets.value = true;
  try {
    const { data } = await listDatasets({
      keyword: keyword.value || undefined,
      limit: datasetPageSize.value,
      offset: (datasetPage.value - 1) * datasetPageSize.value,
    });
    datasets.value = data.items;
    totalDatasets.value = data.total;
  } catch (e) {
    ElMessage.error('获取数据集列表失败');
  } finally {
    loadingDatasets.value = false;
  }
};

const handleDatasetPageChange = () => {
  fetchDatasets();
};

const handleDatasetSizeChange = () => {
  datasetPage.value = 1;
  fetchDatasets();
};

const handleExport = async (datasetId: string, format: 'jsonl' | 'csv') => {
  try {
    const { data } = await exportDataset(datasetId, format);
    const blob = new Blob([data], {
      type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dataset-${datasetId}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    ElMessage.error('导出数据集失败');
  }
};

const handleDelete = async (datasetId: string) => {
  try {
    await deleteDataset(datasetId);
    ElMessage.success('已删除数据集');
    fetchDatasets();
  } catch (e) {
    ElMessage.error('删除失败');
  }
};

onMounted(() => {
  fetchDatasets();
});
</script>
