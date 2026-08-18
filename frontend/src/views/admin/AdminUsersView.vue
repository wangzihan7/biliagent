<template>
  <div class="space-y-5">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'TopicList' }">课题工作台</el-breadcrumb-item>
      <el-breadcrumb-item>系统管理</el-breadcrumb-item>
      <el-breadcrumb-item>用户管理</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-sm font-medium text-slate-900">用户列表</div>
            <div class="text-xs text-slate-500">
              近 {{ logsLimit }} 条日志实时统计活跃度，支持快速筛选与重置密码
            </div>
          </div>
          <div class="flex items-center gap-2">
            <el-input
              v-model="keyword"
              size="small"
              placeholder="按用户、邮箱、角色搜索"
              clearable
              class="w-64"
            />
            <el-button size="small" @click="fetchAll">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loadingUsers"
        :data="filteredUsers"
        border
        size="small"
        class="rounded-xl"
      >
        <el-table-column prop="user_name" label="用户名" min-width="160" />
        <el-table-column prop="email" label="邮箱" min-width="200">
          <template #default="{ row }">
            {{ row.email || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.role === 'admin' ? 'success' : 'info'"
              size="small"
              effect="light"
            >
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近活跃" min-width="160">
          <template #default="{ row }">
            {{ formatTime(getStats(row.user_id).lastActive) }}
          </template>
        </el-table-column>
        <el-table-column label="近日志统计" min-width="180">
          <template #default="{ row }">
            <div class="text-xs text-slate-700 space-y-1">
              <div>查询：{{ getStats(row.user_id).queries }} 次</div>
              <div>爬虫：{{ getStats(row.user_id).crawls }} 次</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleResetPassword(row.user_id, row.user_name)"
            >
              重置密码
            </el-button>
            <el-button type="primary" link size="small" @click="openDetail(row)">
              查看详情
            </el-button>
            <el-button type="info" link size="small" @click="copyUserId(row.user_id)">
              复制 ID
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      :with-header="true"
      :title="detailUser?.user_name ? `${detailUser.user_name} 的概览` : '用户概览'"
      size="50%"
    >
      <div v-if="detailUser" class="space-y-4">
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div class="text-sm font-medium text-slate-900">{{ detailUser.user_name }}</div>
              <div class="text-xs text-slate-500">ID：{{ detailUser.user_id }}</div>
            </div>
            <el-tag
              :type="detailUser.role === 'admin' ? 'success' : 'info'"
              size="small"
              effect="light"
            >
              {{ detailUser.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </div>
          <div class="mt-3 grid gap-2 text-xs text-slate-700 md:grid-cols-2">
            <div>邮箱：{{ detailUser.email || '未填写' }}</div>
            <div>创建时间：{{ formatTime(detailUser.create_time) }}</div>
            <div>最近活跃：{{ formatTime(getStats(detailUser.user_id).lastActive) }}</div>
            <div>
              近日志统计：查询 {{ getStats(detailUser.user_id).queries }} 次 / 爬虫
              {{ getStats(detailUser.user_id).crawls }} 次
            </div>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
              <span>最近查询日志</span>
              <span>显示 {{ detailQueryLogs.length }} 条</span>
            </div>
            <el-table
              :data="detailQueryLogs"
              size="small"
              height="260"
              border
              class="rounded-xl"
              v-loading="loadingLogs"
            >
              <el-table-column label="时间" width="140">
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
                  <el-tag v-else size="small" type="danger" effect="light">失败</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="内容">
                <template #default="{ row }">
                  <span class="text-xs text-slate-700">{{ row.query_text }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div>
            <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
              <span>最近爬虫日志</span>
              <span>显示 {{ detailCrawlLogs.length }} 条</span>
            </div>
            <el-table
              :data="detailCrawlLogs"
              size="small"
              height="260"
              border
              class="rounded-xl"
              v-loading="loadingLogs"
            >
              <el-table-column label="时间" width="140">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="keyword" label="关键词" min-width="120" />
              <el-table-column label="状态" width="80">
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
                  <el-tag v-else size="small" type="danger" effect="light">失败</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <div v-else class="text-xs text-slate-500">请选择一个用户查看详情</div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { listUsers, resetUserPassword } from '@/api/admin';
import { getAdminCrawlLogs, getAdminQueryLogs } from '@/api/logs';
import type { CrawlLogItem, QueryLogItem, User } from '@/types/api';

const users = ref<User[]>([]);
const loadingUsers = ref(false);
const loadingLogs = ref(false);
const keyword = ref('');

const logsLimit = 100;
const queryLogs = ref<QueryLogItem[]>([]);
const crawlLogs = ref<CrawlLogItem[]>([]);

const detailVisible = ref(false);
const detailUser = ref<User | null>(null);

const formatTime = (val?: string | null) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const statsByUser = computed(() => {
  const stats = new Map<
    string,
    { queries: number; crawls: number; lastActive?: string | null }
  >();

  const merge = (userId: string, type: 'queries' | 'crawls', time?: string | null) => {
    const current = stats.get(userId) || { queries: 0, crawls: 0, lastActive: null };
    current[type] += 1;
    if (!current.lastActive || (time && new Date(time) > new Date(current.lastActive))) {
      current.lastActive = time || null;
    }
    stats.set(userId, current);
  };

  queryLogs.value.forEach((log) => merge(log.user_id, 'queries', log.created_at));
  crawlLogs.value.forEach((log) => merge(log.user_id, 'crawls', log.created_at));

  return stats;
});

const getStats = (userId: string) =>
  statsByUser.value.get(userId) || { queries: 0, crawls: 0, lastActive: null };

const filteredUsers = computed(() => {
  if (!keyword.value.trim()) return users.value;
  const k = keyword.value.toLowerCase();
  return users.value.filter(
    (u) =>
      u.user_name.toLowerCase().includes(k) ||
      (u.email || '').toLowerCase().includes(k) ||
      u.role.toLowerCase().includes(k),
  );
});

const fetchUsers = async () => {
  loadingUsers.value = true;
  try {
    const { data } = await listUsers({ skip: 0, limit: logsLimit });
    users.value = data;
  } catch (e) {
    ElMessage.error('获取用户列表失败');
  } finally {
    loadingUsers.value = false;
  }
};

const fetchLogs = async () => {
  loadingLogs.value = true;
  try {
    const [{ data: queries }, { data: crawls }] = await Promise.all([
      getAdminQueryLogs({ limit: logsLimit }),
      getAdminCrawlLogs({ limit: logsLimit, offset: 0 }),
    ]);
    queryLogs.value = queries;
    crawlLogs.value = crawls.items;
  } catch (e) {
    ElMessage.error('获取日志失败');
  } finally {
    loadingLogs.value = false;
  }
};

const fetchAll = () => {
  fetchUsers();
  fetchLogs();
};

const handleResetPassword = async (userId: string, userName: string) => {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入用户「${userName}」的新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '至少 6 位',
        inputType: 'password',
      },
    );
    if (!value || value.length < 6) {
      ElMessage.warning('密码长度需至少 6 位');
      return;
    }
    await resetUserPassword(userId, value);
    ElMessage.success('密码已重置');
  } catch (e) {
    // 用户取消或接口错误均忽略
  }
};

const openDetail = (user: User) => {
  detailUser.value = user;
  detailVisible.value = true;
};

const copyUserId = async (userId: string) => {
  try {
    await navigator.clipboard.writeText(userId);
    ElMessage.success('用户 ID 已复制');
  } catch (err) {
    console.error(err);
    ElMessage.error('复制失败，请手动选择文本');
  }
};

const detailQueryLogs = computed(() =>
  queryLogs.value.filter((log) => log.user_id === detailUser.value?.user_id).slice(0, 30),
);

const detailCrawlLogs = computed(() =>
  crawlLogs.value.filter((log) => log.user_id === detailUser.value?.user_id).slice(0, 30),
);

onMounted(() => {
  fetchAll();
});
</script>
