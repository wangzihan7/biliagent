<template>
  <div class="space-y-5">
    <section
      class="overflow-hidden rounded-2xl bg-gradient-to-r from-[#E3F0FF] via-[#EDEBFF] to-[#E5FBFF] px-6 py-5 shadow-sm"
    >
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 tracking-tight">爬虫管理</h1>
          <p class="mt-1 text-sm text-slate-600">
            创建并查看 B 站采集任务，支持控制评论/弹幕数量，实时查看任务日志。
          </p>
        </div>
        <div class="flex flex-col items-end gap-2 text-xs text-slate-500">
          <span>爬虫日志支持分页查看</span>
        </div>
      </div>
    </section>

    <section class="grid gap-5 lg:grid-cols-3">
      <el-card shadow="never" class="!rounded-2xl !border-none !bg-white lg:col-span-1">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-900">新建爬虫任务</span>
          </div>
        </template>
        <el-form
          ref="crawlFormRef"
          :model="crawlForm"
          :rules="crawlRules"
          label-width="82px"
          size="small"
        >
          <el-form-item label="关键词" prop="keyword">
            <el-input v-model="crawlForm.keyword" placeholder="例如：成都火锅" />
          </el-form-item>
          <el-form-item label="页码" prop="page">
            <el-input-number v-model="crawlForm.page" :min="1" :max="50" />
          </el-form-item>
          <el-form-item label="最大条数" prop="max_items">
            <el-input-number v-model="crawlForm.max_items" :min="1" :max="500" :step="10" />
          </el-form-item>
          <el-form-item label="评论上限" prop="max_comments">
            <el-input-number v-model="crawlForm.max_comments" :min="0" :max="5000" :step="10" />
          </el-form-item>
          <el-form-item label="回复上限" prop="max_replies">
            <el-input-number v-model="crawlForm.max_replies" :min="0" :max="100" />
          </el-form-item>
          <el-form-item label="评论页数" prop="max_comment_pages">
            <el-input-number v-model="crawlForm.max_comment_pages" :min="1" :max="50" />
          </el-form-item>
          <el-form-item label="弹幕上限" prop="max_danmaku">
            <el-input-number v-model="crawlForm.max_danmaku" :min="0" :max="5000" :step="10" />
          </el-form-item>
          <el-form-item label="数据集名称" prop="dataset_name">
            <el-input v-model="crawlForm.dataset_name" placeholder="用于标记本次采集的数据集" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creatingCrawl" @click="handleCreateCrawl">开始采集</el-button>
          </el-form-item>
        </el-form>
        <p class="mt-2 text-[11px] text-slate-400">提示：采集会消耗配额，建议从较小的 max_items 开始测试。</p>
      </el-card>

      <el-card shadow="never" class="!rounded-2xl !border-none !bg-white lg:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-900">
              {{ auth.isAdmin ? '全部爬虫日志' : '我的爬虫日志' }}
            </span>
            <el-button size="small" @click="fetchCrawlLogs">刷新</el-button>
          </div>
        </template>
        <el-table v-loading="loadingLogs" :data="crawlLogs" border size="small" class="rounded-xl">
          <el-table-column prop="keyword" label="关键词" min-width="160" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'success'" size="small" type="success" effect="light">成功</el-tag>
              <el-tag v-else-if="row.status === 'running'" size="small" type="warning" effect="light">进行中</el-tag>
              <el-tag v-else size="small" type="danger" effect="light">失败</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="video_count" label="视频数" width="80" />
          <el-table-column prop="comment_count" label="评论数" width="80" />
          <el-table-column prop="danmaku_count" label="弹幕数" width="80" />
          <el-table-column label="时间" min-width="160">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="错误信息" min-width="200">
            <template #default="{ row }">
              <span class="text-xs text-rose-500">{{ row.error_msg || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="mt-3 flex justify-end">
          <el-pagination
            v-model:current-page="logPage"
            v-model:page-size="logPageSize"
            background
            layout="prev, pager, next, sizes, total"
            :total="totalCrawlLogs"
            :page-sizes="[10, 20, 50]"
            @current-change="handleLogPageChange"
            @size-change="handleLogSizeChange"
          />
        </div>
      </el-card>
    </section>

  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import { createCrawlTask } from '@/api/datasets';
import { getMyCrawlLogs, getAdminCrawlLogs } from '@/api/logs';
import { useAuthStore } from '@/stores/auth';
import type { CrawlLogItem } from '@/types/api';

const auth = useAuthStore();
const crawlFormRef = ref<FormInstance>();
const crawlForm = reactive({
  keyword: '',
  page: 1,
  max_items: 50,
  dataset_name: '',
  max_comments: 10,
  max_replies: 3,
  max_comment_pages: 1,
  max_danmaku: 50,
});

const crawlRules: FormRules = {
  keyword: [{ required: true, message: '请填写关键词', trigger: 'blur' }],
  page: [{ required: true, message: '请填写页码', trigger: 'change' }],
  max_items: [{ required: true, message: '请填写最大条数', trigger: 'change' }],
  dataset_name: [{ required: true, message: '请填写数据集名称', trigger: 'blur' }],
  max_comments: [{ required: true, message: '请填写评论上限', trigger: 'change' }],
  max_replies: [{ required: true, message: '请填写回复上限', trigger: 'change' }],
  max_comment_pages: [{ required: true, message: '请填写评论页数', trigger: 'change' }],
  max_danmaku: [{ required: true, message: '请填写弹幕上限', trigger: 'change' }],
};

const creatingCrawl = ref(false);

const crawlLogs = ref<CrawlLogItem[]>([]);
const totalCrawlLogs = ref(0);
const loadingLogs = ref(false);
const logPage = ref(1);
const logPageSize = ref(10);

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const handleCreateCrawl = () => {
  if (!crawlFormRef.value) return;
  crawlFormRef.value.validate(async (valid) => {
    if (!valid) return;
    creatingCrawl.value = true;
    try {
      await createCrawlTask({
        keyword: crawlForm.keyword,
        page: crawlForm.page,
        max_items: crawlForm.max_items,
        dataset_name: crawlForm.dataset_name || crawlForm.keyword,
        max_comments: crawlForm.max_comments,
        max_replies: crawlForm.max_replies,
        max_comment_pages: crawlForm.max_comment_pages,
        max_danmaku: crawlForm.max_danmaku,
      });
      ElMessage.success('爬虫任务已创建');
      logPage.value = 1;
      fetchCrawlLogs();
    } catch (e) {
      ElMessage.error('创建爬虫任务失败');
    } finally {
      creatingCrawl.value = false;
    }
  });
};

const fetchCrawlLogs = async () => {
  loadingLogs.value = true;
  try {
    const api = auth.isAdmin ? getAdminCrawlLogs : getMyCrawlLogs;
    const { data } = await api({
      limit: logPageSize.value,
      offset: (logPage.value - 1) * logPageSize.value,
    });
    crawlLogs.value = data.items;
    totalCrawlLogs.value = data.total;
  } catch (e) {
    ElMessage.error('获取爬虫日志失败');
  } finally {
    loadingLogs.value = false;
  }
};

const handleLogPageChange = () => {
  fetchCrawlLogs();
};

const handleLogSizeChange = () => {
  logPage.value = 1;
  fetchCrawlLogs();
};

onMounted(() => {
  fetchCrawlLogs();
});
</script>
