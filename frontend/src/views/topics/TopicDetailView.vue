<template>
  <div class="space-y-5">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'TopicList' }">课题工作台</el-breadcrumb-item>
      <el-breadcrumb-item>{{ topic?.name || '课题详情' }}</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 课题概要卡片 -->
    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <h2 class="text-xl font-semibold text-slate-900 truncate">
            {{ topic?.name || '课题详情' }}
          </h2>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <el-tag size="small" effect="light" type="primary">
              {{ topic?.topic_type || '未分类' }}
            </el-tag>
          </div>
          <p class="mt-3 text-sm text-slate-600 whitespace-pre-line">
            {{
              topic?.description ||
                '暂无课题描述，可在编辑中补充研究范围与目的。'
            }}
          </p>
          <div class="mt-3 flex flex-wrap items-center gap-4 text-[11px] text-slate-500">
            <span>创建时间：{{ formatTime(topic?.created_at) }}</span>
            <span>最近更新：{{ formatTime(topic?.updated_at) }}</span>
          </div>
        </div>
        <div class="flex flex-col items-end gap-2">
          <el-button type="primary" size="small" round @click="handleCreateConversation">
            新建会话
          </el-button>
          <el-button size="small" round plain @click="goReport">
            查看课题报告
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Tabs 内容 -->
    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <el-tabs v-model="activeTab">
        <!-- 会话 Tab -->
        <el-tab-pane label="会话" name="sessions">
          <div v-if="!topic?.conversations?.length" class="text-sm text-slate-500">
            当前课题还没有会话，可以通过右上角「新建会话」按钮创建。
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="conv in topic?.conversations"
              :key="conv.conversation_id"
              class="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs cursor-pointer hover:bg-sky-50 transition-colors"
              @click="goConversation(conv.conversation_id)"
            >
              <div class="min-w-0">
                <p class="font-medium text-slate-900 truncate">
                  {{ conv.conversation_name || '未命名会话' }}
                </p>
                <p class="mt-1 text-[11px] text-slate-500">
                  更新于：{{ formatTime(conv.update_time) }}
                </p>
              </div>
              <el-button type="primary" text size="small">进入分析</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据集 Tab -->
        <el-tab-pane label="数据集" name="datasets">
          <div class="flex items-center justify-between mb-3 text-xs text-slate-500">
            <p>
              展示当前课题已经绑定的数据集，可用于离线模式回答与报告生成。
            </p>
            <div class="flex items-center gap-2">
              <el-button size="small" round @click="openBindDatasetDialog">
                绑定已有数据集
              </el-button>
            </div>
          </div>

          <el-empty
            v-if="!topic?.datasets?.length"
            description="当前课题尚未绑定数据集"
          >
            <el-button size="small" type="primary" round @click="openBindDatasetDialog">
              绑定数据集
            </el-button>
          </el-empty>

          <el-table
            v-else
            :data="topic?.datasets || []"
            border
            size="small"
            class="rounded-xl"
          >
            <el-table-column prop="name" label="数据集名称" min-width="160" />
            <el-table-column prop="keyword" label="关键词" min-width="140" />
            <el-table-column prop="video_count" label="视频数" width="80" />
            <el-table-column prop="comment_count" label="评论数" width="80" />
            <el-table-column prop="danmaku_count" label="弹幕数" width="80" />
            <el-table-column label="创建时间" min-width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 报告 Tab -->
        <el-tab-pane label="报告" name="report">
          <div class="mb-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <p>
              图表与洞察来自 <code class="text-[11px]">/topics/{{ topicId }}/report</code>，
              关键回答可在聊天页星标后汇总到此处。
            </p>
            <div class="flex items-center gap-2">
              <el-button size="small" round plain :loading="reportLoading" @click="handleRefreshReport">
                刷新报告
              </el-button>
              <el-button size="small" round plain type="primary" @click="handleExportReport">
                导出报告（Markdown）
              </el-button>
            </div>
          </div>

          <el-skeleton v-if="reportLoading" :rows="6" animated />
          <el-empty v-else-if="reportError" :description="reportError">
            <el-button size="small" type="primary" round @click="fetchReport(true)">
              重新获取
            </el-button>
          </el-empty>
          
          <template v-else-if="report">
            <TopicReportCharts :report="report" />

            <section class="mt-6 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
              <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h4 class="text-base font-semibold text-slate-900">关键回答</h4>
                  <p class="text-xs text-slate-500">
                    在聊天页为助手回答点击「设为关键回答」，可快速沉淀研究要点
                  </p>
                </div>
                <span v-if="report.key_answers?.length" class="text-xs text-slate-400">
                  共 {{ report.key_answers.length }} 条
                </span>
              </div>
              <el-empty
                v-if="!report.key_answers?.length"
                description="暂无关键回答，请在聊天记录中标记需要沉淀的答复"
              />
              <div v-else class="space-y-3">
                <el-card
                  v-for="item in report.key_answers"
                  :key="item.message_id"
                  shadow="never"
                  class="!rounded-2xl !border-slate-200"
                  :body-style="{ padding: '16px' }"
                >
                  <div class="flex flex-wrap items-center justify-between gap-3 text-sm">
                    <div>
                      <p class="font-medium text-slate-900">
                        {{ item.conversation_name || '关键回答' }}
                      </p>
                      <p class="mt-0.5 text-[11px] text-slate-500">
                        {{ formatTime(item.created_at) }}
                      </p>
                    </div>
                    <el-button
                      type="primary"
                      text
                      size="small"
                      @click="handleKeyAnswerClick(item.conversation_id)"
                    >
                      前往会话
                    </el-button>
                  </div>
                  <div
                    class="mt-3 text-sm leading-relaxed text-slate-700 break-words markdown-body"
                    v-html="renderMarkdown(item.content)"
                  />
                  <div v-if="(item.content || '').length > 400" class="mt-2 text-right">
                    <el-button type="primary" link size="small" @click="showAnswerDetail(item)">
                      查看详情
                    </el-button>
                  </div>
                </el-card>
              </div>
            </section>
          </template>
          <el-empty
            v-else
            description="暂无报告数据，可结合会话与数据集分析后再试"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      v-model="answerDetailVisible"
      :title="answerDetail?.conversation_name || '关键回答'"
      width="720px"
      destroy-on-close
    >
      <div class="markdown-body text-sm leading-relaxed">
        <div v-html="answerDetail ? renderMarkdown(answerDetail.content) : ''" />
      </div>
      <template #footer>
        <el-button @click="answerDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 绑定已有数据集对话框 -->
    <el-dialog
      v-model="bindDialogVisible"
      title="绑定已有数据集"
      width="480px"
    >
      <el-form label-width="80px">
        <el-form-item label="选择数据集">
          <el-select
            v-model="selectedDatasetId"
            filterable
            placeholder="请选择要绑定的数据集"
            class="w-full"
          >
            <el-option
              v-for="ds in availableDatasets"
              :key="ds.dataset_id"
              :label="`${ds.name}（${ds.keyword}）`"
              :value="ds.dataset_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="binding"
          :disabled="!selectedDatasetId"
          @click="handleBindDataset"
        >
          确定绑定
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { getTopic, bindDatasetToTopic, startTopicReport, getTopicReportTask } from '@/api/topics';
import { createConversation } from '@/api/conversations';
import { listDatasets } from '@/api/datasets';
import { useAuthStore } from '@/stores/auth';
import type { DatasetSummary, TopicDetail, TopicReport } from '@/types/api';
import TopicReportCharts from './TopicReportCharts.vue';
import http from '@/api/http';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const topicId = route.params.topicId as string;

const topic = ref<TopicDetail | null>(null);
const activeTab = ref((route.query.tab as string) || 'sessions');

const allDatasets = ref<DatasetSummary[]>([]);

// 绑定数据集弹窗状态
const bindDialogVisible = ref(false);
const selectedDatasetId = ref<string>('');
const binding = ref(false);

const availableDatasets = computed(() => {
  if (!topic.value) return allDatasets.value;
  const boundIds = new Set(topic.value.datasets.map((d) => d.dataset_id));
  return allDatasets.value.filter((d) => !boundIds.has(d.dataset_id));
});

const fetchDetail = async () => {
  try {
    const { data } = await getTopic(topicId);
    topic.value = data;
  } catch (e) {
    ElMessage.error('获取课题详情失败');
  }
};

const fetchAllDatasets = async () => {
  try {
    const { data } = await listDatasets({ limit: 100, offset: 0 });
    allDatasets.value = data.items;
  } catch {
    // 忽略失败，绑定对话框中会提示无可用数据集
  }
};

const report = ref<TopicReport | null>(null);
const reportLoading = ref(false);
const reportError = ref<string | null>(null);
const reportRequested = ref(false);
const reportPollTimer = ref<number | null>(null);

const md = new MarkdownIt({ linkify: true, breaks: true });
const defaultLinkOpen =
  md.renderer.rules.link_open ||
  function (tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const aIndex = tokens[idx].attrIndex('target');
  if (aIndex < 0) tokens[idx].attrPush(['target', '_blank']);
  else tokens[idx].attrs![aIndex][1] = '_blank';
  tokens[idx].attrPush(['rel', 'noopener noreferrer']);
  return defaultLinkOpen(tokens, idx, options, env, self);
};
const renderMarkdown = (text: string) =>
  DOMPurify.sanitize(md.render(text || ''), { ADD_ATTR: ['target', 'rel'] });

const answerDetailVisible = ref(false);
const answerDetail = ref<any>(null);
const showAnswerDetail = (item: any) => {
  answerDetail.value = item;
  answerDetailVisible.value = true;
};

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const goReport = () => {
  activeTab.value = 'report';
};

const clearReportPoll = () => {
  if (reportPollTimer.value !== null) {
    window.clearTimeout(reportPollTimer.value);
    reportPollTimer.value = null;
  }
};

const scheduleReportPoll = () => {
  clearReportPoll();
  reportPollTimer.value = window.setTimeout(() => {
    pollReportStatus();
  }, 2000);
};

const pollReportStatus = async () => {
  try {
    const { data } = await getTopicReportTask(topicId);
    if (data.status === 'success' && data.report) {
      report.value = data.report;
      reportLoading.value = false;
      reportRequested.value = true;
      clearReportPoll();
      return;
    }
    if (data.status === 'failed') {
      reportError.value = data.error || '课题报告生成失败，请稍后重试';
      reportLoading.value = false;
      reportRequested.value = true;
      clearReportPoll();
      return;
    }
    if (data.status === 'missing') {
      await fetchReport(true);
      return;
    }
  } catch (e) {
    reportError.value = '获取课题报告状态失败，请稍后重试';
    reportLoading.value = false;
    reportRequested.value = true;
    clearReportPoll();
    return;
  }
  scheduleReportPoll();
};

const fetchReport = async (force = false) => {
  if (reportLoading.value && !force) return;
  reportLoading.value = true;
  reportError.value = null;
  reportRequested.value = true;
  try {
    const { data } = await startTopicReport(topicId, force);
    if (data.status === 'success' && data.report) {
      report.value = data.report;
      reportLoading.value = false;
      clearReportPoll();
      return;
    }
    if (data.status === 'failed') {
      reportError.value = data.error || '课题报告生成失败，请稍后重试';
      reportLoading.value = false;
      clearReportPoll();
      return;
    }
    scheduleReportPoll();
  } catch (e) {
    reportError.value = '获取课题报告失败，请稍后重试';
    reportLoading.value = false;
    clearReportPoll();
  }
};

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && tab !== activeTab.value) {
      activeTab.value = tab;
    }
  },
);

watch(
  () => activeTab.value,
  (tab) => {
    if (route.query.tab !== tab) {
      router.replace({
        name: route.name as string,
        params: route.params,
        query: { ...route.query, tab },
      });
    }
    if (tab === 'report' && !reportRequested.value) {
      fetchReport();
    }
  },
  { immediate: true },
);

const goConversation = (conversationId: string) => {
  router.push({ name: 'Chat', params: { conversationId } });
};

const handleCreateConversation = async () => {
  if (!auth.userId) {
    ElMessage.error('请先登录');
    return;
  }
  try {
    const { data } = await createConversation({
      user_id: auth.userId,
      conversation_name: `${topic.value?.name || '新课题会话'}`,
      topic_id: topicId,
    });
    // 更新本地 topic 会话列表
    if (topic.value) {
      topic.value.conversations = [data, ...topic.value.conversations];
    }
    goConversation(data.conversation_id);
  } catch (e) {
    ElMessage.error('创建会话失败');
  }
};

const openBindDatasetDialog = async () => {
  await fetchAllDatasets();
  selectedDatasetId.value = '';
  bindDialogVisible.value = true;
};

const handleBindDataset = async () => {
  if (!selectedDatasetId.value) return;
  binding.value = true;
  try {
    await bindDatasetToTopic(topicId, selectedDatasetId.value);
    ElMessage.success('数据集已绑定到课题');
    bindDialogVisible.value = false;
    await fetchDetail();
  } catch (e) {
    ElMessage.error('绑定数据集失败');
  } finally {
    binding.value = false;
  }
};

const handleKeyAnswerClick = (conversationId: string) => {
  if (!conversationId) return;
  router.push({ name: 'Chat', params: { conversationId } });
};

const handleRefreshReport = () => {
  fetchReport(true);
};

const handleExportReport = () => {
  // 使用带 token 的 http 实例下载，避免未携带 Authorization
  http
    .get(`/topics/${topicId}/report.md`, {
      responseType: 'blob',
      timeout: 120000, // 导出可能耗时，适当放宽超时时间
    })
    .then((res) => {
      const blob = new Blob([res.data], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${topic.value?.name || 'topic-report'}.md`;
      a.click();
      URL.revokeObjectURL(url);
    })
    .catch(() => {
      ElMessage.error('导出报告失败，请稍后再试');
    });
};

onMounted(() => {
  fetchDetail();
});

onBeforeUnmount(() => {
  clearReportPoll();
});
</script>
