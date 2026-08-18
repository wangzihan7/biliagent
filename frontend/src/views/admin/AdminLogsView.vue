<template>
  <div class="space-y-5">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'TopicList' }">课题工作台</el-breadcrumb-item>
      <el-breadcrumb-item>系统管理</el-breadcrumb-item>
      <el-breadcrumb-item>审计日志</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="查询日志（全部）" name="admin-query">
          <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
            <span>展示最近 {{ limit }} 条查询日志</span>
            <el-button size="small" @click="fetchAdminQueryLogs">刷新</el-button>
          </div>
          <el-table
            v-loading="loadingAdminQuery"
            :data="adminQueryLogs"
            border
            size="small"
            class="rounded-xl"
          >
            <el-table-column prop="user_id" label="用户 ID" min-width="120" />
            <el-table-column prop="topic_id" label="课题 ID" min-width="120" />
            <el-table-column prop="conversation_id" label="会话 ID" min-width="120" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  v-if="row.status === 'success'"
                  type="success"
                  size="small"
                  effect="light"
                >
                  成功
                </el-tag>
                <el-tag v-else size="small" type="danger" effect="light">
                  失败
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" min-width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="查询内容" min-width="260">
              <template #default="{ row }">
                <span class="text-xs text-slate-700">
                  {{ row.query_text }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="错误信息" min-width="200">
              <template #default="{ row }">
                <span class="text-xs text-rose-500">
                  {{ row.error_msg || '-' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="爬虫日志（全部）" name="admin-crawl">
          <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
            <span>展示最近 {{ limit }} 条爬虫日志</span>
            <el-button size="small" @click="fetchAdminCrawlLogs">刷新</el-button>
          </div>
          <el-table
            v-loading="loadingAdminCrawl"
            :data="adminCrawlLogs"
            border
            size="small"
            class="rounded-xl"
          >
            <el-table-column prop="user_id" label="用户 ID" min-width="120" />
            <el-table-column prop="keyword" label="关键词" min-width="160" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  v-if="row.status === 'success'"
                  size="small"
                  type="success"
                  effect="light"
                >
                  成功
                </el-tag>
                <el-tag
                  v-else-if="row.status === 'running'"
                  size="small"
                  type="warning"
                  effect="light"
                >
                  进行中
                </el-tag>
                <el-tag v-else size="small" type="danger" effect="light">
                  失败
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" min-width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="video_count" label="视频数" width="80" />
            <el-table-column prop="comment_count" label="评论数" width="80" />
            <el-table-column prop="danmaku_count" label="弹幕数" width="80" />
            <el-table-column label="错误信息" min-width="200">
              <template #default="{ row }">
                <span class="text-xs text-rose-500">
                  {{ row.error_msg || '-' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="我的日志" name="mine">
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
                <span>我的查询日志</span>
                <el-button size="small" @click="fetchMyQueryLogs">刷新</el-button>
              </div>
              <el-table
                v-loading="loadingMyQuery"
                :data="myQueryLogs"
                border
                size="small"
                class="rounded-xl"
              >
                <el-table-column label="时间" min-width="140">
                  <template #default="{ row }">
                    {{ formatTime(row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="70">
                  <template #default="{ row }">
                    <el-tag
                      v-if="row.status === 'success'"
                      size="small"
                      type="success"
                      effect="light"
                    >
                      成功
                    </el-tag>
                    <el-tag v-else size="small" type="danger" effect="light">
                      失败
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="内容" min-width="200">
                  <template #default="{ row }">
                    <span class="text-xs text-slate-700">
                      {{ row.query_text }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div>
              <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
                <span>我的爬虫日志</span>
                <el-button size="small" @click="fetchMyCrawlLogs">刷新</el-button>
              </div>
              <el-table
                v-loading="loadingMyCrawl"
                :data="myCrawlLogs"
                border
                size="small"
                class="rounded-xl"
              >
                <el-table-column label="时间" min-width="140">
                  <template #default="{ row }">
                    {{ formatTime(row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column prop="keyword" label="关键词" min-width="140" />
                <el-table-column label="状态" width="70">
                  <template #default="{ row }">
                    <el-tag
                      v-if="row.status === 'success'"
                      size="small"
                      type="success"
                      effect="light"
                    >
                      成功
                    </el-tag>
                    <el-tag
                      v-else-if="row.status === 'running'"
                      size="small"
                      type="warning"
                      effect="light"
                    >
                      进行中
                    </el-tag>
                    <el-tag v-else size="small" type="danger" effect="light">
                      失败
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  getAdminCrawlLogs,
  getAdminQueryLogs,
  getMyCrawlLogs,
  getMyQueryLogs,
} from '@/api/logs';
import type { CrawlLogItem, QueryLogItem } from '@/types/api';

const limit = 100;
const activeTab = ref<'admin-query' | 'admin-crawl' | 'mine'>('admin-query');

const adminQueryLogs = ref<QueryLogItem[]>([]);
const adminCrawlLogs = ref<CrawlLogItem[]>([]);
const myQueryLogs = ref<QueryLogItem[]>([]);
const myCrawlLogs = ref<CrawlLogItem[]>([]);

const loadingAdminQuery = ref(false);
const loadingAdminCrawl = ref(false);
const loadingMyQuery = ref(false);
const loadingMyCrawl = ref(false);

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const fetchAdminQueryLogs = async () => {
  loadingAdminQuery.value = true;
  try {
    const { data } = await getAdminQueryLogs({ limit });
    adminQueryLogs.value = data;
  } catch (e) {
    ElMessage.error('获取查询日志失败');
  } finally {
    loadingAdminQuery.value = false;
  }
};

const fetchAdminCrawlLogs = async () => {
  loadingAdminCrawl.value = true;
  try {
    const { data } = await getAdminCrawlLogs({ limit, offset: 0 });
    adminCrawlLogs.value = data.items;
  } catch (e) {
    ElMessage.error('获取爬虫日志失败');
  } finally {
    loadingAdminCrawl.value = false;
  }
};

const fetchMyQueryLogs = async () => {
  loadingMyQuery.value = true;
  try {
    const { data } = await getMyQueryLogs({ limit: 50 });
    myQueryLogs.value = data;
  } catch (e) {
    ElMessage.error('获取我的查询日志失败');
  } finally {
    loadingMyQuery.value = false;
  }
};

const fetchMyCrawlLogs = async () => {
  loadingMyCrawl.value = true;
  try {
    const { data } = await getMyCrawlLogs({ limit: 50, offset: 0 });
    myCrawlLogs.value = data.items;
  } catch (e) {
    ElMessage.error('获取我的爬虫日志失败');
  } finally {
    loadingMyCrawl.value = false;
  }
};

onMounted(() => {
  fetchAdminQueryLogs();
  fetchAdminCrawlLogs();
  fetchMyQueryLogs();
  fetchMyCrawlLogs();
});
</script>
