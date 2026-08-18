<template>
  <div class="space-y-5">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'TopicList' }">课题工作台</el-breadcrumb-item>
      <el-breadcrumb-item>课题报告总览</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">最近课题报告</h2>
          <p class="mt-1 text-sm text-slate-500">
            汇总近期课题的关键指标与模型洞察，可直接跳转到具体课题的报告页。
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <el-input
            v-model="keyword"
            size="small"
            placeholder="搜索课题名称 / 描述"
            clearable
            class="w-56"
          >
            <template #prefix>
              <el-icon><i-ep-search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="typeFilter"
            size="small"
            placeholder="课题类型"
            style="width: 160px"
            clearable
          >
            <el-option label="全部类型" value="" />
            <el-option
              v-for="type in topicTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
          <el-select
            v-model="sortOrder"
            size="small"
            style="width: 160px"
          >
            <el-option label="按更新时间（近到远）" value="desc" />
            <el-option label="按更新时间（远到近）" value="asc" />
          </el-select>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-900">课题列表</h3>
          <span class="text-xs text-slate-400">
            共 {{ filteredTopics.length }} 个课题（第 {{ currentPage }} 页）
          </span>
        </div>
      </template>

      <el-skeleton v-if="loadingTopics" animated :rows="4" />
      <el-empty
        v-else-if="!filteredTopics.length"
        description="暂无满足条件的课题，可尝试调整筛选。"
      />
      <div v-else class="grid gap-4 2xl:grid-cols-2">
        <el-card
          v-for="topic in pagedTopics"
          :key="topic.topic_id"
          shadow="never"
          class="!rounded-2xl !border-slate-200"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h4 class="text-base font-semibold text-slate-900 truncate">
                  {{ topic.name }}
                </h4>
                <el-tag size="small" effect="light" round>
                  {{ topic.topic_type || '未归类' }}
                </el-tag>
              </div>
              <p class="mt-2 text-xs text-slate-500">
                {{ formatTime(topic.created_at) }} 创建 · {{ formatTime(topic.updated_at) }} 更新
              </p>
              <p class="mt-3 text-sm text-slate-600 line-clamp-2">
                {{ topic.description || '暂无课题描述' }}
              </p>
            </div>
            <div class="flex flex-col gap-2">
              <el-button
                size="small"
                round
                type="primary"
                plain
                @click="goTopicReport(topic.topic_id)"
              >
                查看报告
              </el-button>
              <el-button
                size="small"
                round
                text
                @click="toggleExpand(topic.topic_id)"
              >
                {{ isExpanded(topic.topic_id) ? '收起概览' : '展开概览' }}
              </el-button>
            </div>
          </div>

          <transition name="fade">
            <div
              v-if="isExpanded(topic.topic_id)"
              class="mt-4 rounded-2xl bg-slate-50/80 p-4 max-h-[240px] overflow-auto"
            >
              <template v-if="reportLoadingMap[topic.topic_id]">
                <el-skeleton :rows="4" animated />
              </template>
              <template v-else-if="reportErrorMap[topic.topic_id]">
                <div class="flex items-center justify-between text-sm text-rose-500">
                  <span>{{ reportErrorMap[topic.topic_id] }}</span>
                  <el-button size="small" text type="primary" @click="fetchReport(topic.topic_id, true)">
                    重试
                  </el-button>
                </div>
              </template>
              <template v-else-if="reportMap[topic.topic_id]">
                <div class="grid gap-5 lg:grid-cols-[1.15fr_1fr] items-stretch">
                  <div class="min-w-0 flex flex-col h-full gap-2">
                    <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      模型洞察
                    </p>
                    <div
                      class="mt-1 flex-1 text-[13px] leading-relaxed text-slate-700 markdown-body max-h-28 overflow-auto"
                      v-html="renderMarkdown(reportMap[topic.topic_id]?.llm_summary || reportMap[topic.topic_id]?.summary || '暂无摘要')"
                    />
                    <div class="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
                      <span>
                        数据集：{{ reportMap[topic.topic_id]?.totals?.datasets ?? '--' }}
                      </span>
                      <span>
                        视频数：{{ formatNumber(reportMap[topic.topic_id]?.totals?.videos) }}
                      </span>
                      <span>
                        评论数：{{ formatNumber(reportMap[topic.topic_id]?.totals?.comments) }}
                      </span>
                      <span>
                        弹幕数：{{ formatNumber(reportMap[topic.topic_id]?.totals?.danmaku) }}
                      </span>
                    </div>
                  </div>
                  <div class="space-y-2 text-sm min-w-0 flex flex-col h-full">
                    <div>
                      <p class="text-xs font-semibold text-slate-500">热门标签</p>
                      <div class="mt-1 flex flex-wrap gap-1">
                        <span
                          v-for="tag in (reportMap[topic.topic_id]?.top_tags || []).slice(0, 4)"
                          :key="typeof tag === 'string' ? tag : tag?.name"
                          class="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-600 border border-slate-200"
                        >
                          {{ typeof tag === 'string' ? tag : tag?.name }}
                        </span>
                        <span v-if="!(reportMap[topic.topic_id]?.top_tags?.length)">
                          暂无
                        </span>
                      </div>
                    </div>
                    <div class="flex-1 flex flex-col">
                      <p class="text-xs font-semibold text-slate-500">关键回答</p>
                      <div
                        class="mt-1 flex-1 text-[13px] leading-relaxed text-slate-700 markdown-body max-h-28 overflow-auto pr-1"
                        v-html="renderMarkdown(keyAnswerText(topic.topic_id) || '暂无关键回答')"
                      />
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="text-sm text-slate-500 flex items-center justify-between">
                  <span>尚未加载该课题的报告概览。</span>
                  <el-button size="small" type="primary" round @click="fetchReport(topic.topic_id)">
                    加载报告
                  </el-button>
                </div>
              </template>
            </div>
          </transition>
        </el-card>
      </div>

      <div
        v-if="filteredTopics.length > pageSize"
        class="mt-6 flex justify-end"
      >
        <el-pagination
          background
          layout="prev, pager, next"
          :page-size="pageSize"
          :total="filteredTopics.length"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import { listTopics, startTopicReport, getTopicReportTask } from '@/api/topics';
import type { TopicListItem, TopicReport } from '@/types/api';

const router = useRouter();

const loadingTopics = ref(false);
const topics = ref<TopicListItem[]>([]);
const keyword = ref('');
const typeFilter = ref('');
const sortOrder = ref<'asc' | 'desc'>('desc');
const currentPage = ref(1);
const pageSize = ref(6);

const expandedTopics = ref<string[]>([]);
const reportMap = reactive<Record<string, TopicReport | undefined>>({});
const reportLoadingMap = reactive<Record<string, boolean>>({});
const reportErrorMap = reactive<Record<string, string | null>>({});
const reportPollTimers = new Map<string, number>();

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

const keyAnswerText = (topicId: string) => {
  const answers = reportMap[topicId]?.key_answers || [];
  if (!answers.length) return '';
  return answers
    .map((item, idx) => `${idx + 1}. ${item.content || ''}`)
    .join('\n\n');
};

const loadTopics = async () => {
  loadingTopics.value = true;
  try {
    const { data } = await listTopics({ limit: 100, offset: 0 });
    topics.value = data.items;
  } catch (e) {
    ElMessage.error('获取课题列表失败');
  } finally {
    loadingTopics.value = false;
  }
};

const topicTypes = computed(() => {
  const set = new Set<string>();
  topics.value.forEach((t) => {
    if (t.topic_type) set.add(t.topic_type);
  });
  return Array.from(set);
});

const filteredTopics = computed(() => {
  const filtered = topics.value.filter((topic) => {
    const matchKeyword =
      !keyword.value ||
      topic.name.toLowerCase().includes(keyword.value.toLowerCase()) ||
      (topic.description || '').toLowerCase().includes(keyword.value.toLowerCase());
    const matchType = !typeFilter.value || topic.topic_type === typeFilter.value;
    return matchKeyword && matchType;
  });

  return filtered.sort((a, b) => {
    const aTime = new Date(a.updated_at || a.created_at).getTime();
    const bTime = new Date(b.updated_at || b.created_at).getTime();
    return sortOrder.value === 'desc' ? bTime - aTime : aTime - bTime;
  });
});

const pagedTopics = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredTopics.value.slice(start, start + pageSize.value);
});

const formatTime = (val?: string) => {
  if (!val) return '--';
  return val.replace('T', ' ').split('.')[0];
};

const formatNumber = (val?: number) => {
  if (val === undefined || val === null) return '--';
  return Number(val).toLocaleString();
};

const truncate = (text: string, len = 80) => {
  if (!text) return '';
  if (text.length <= len) return text;
  return `${text.slice(0, len)}...`;
};

const isExpanded = (topicId: string) => expandedTopics.value.includes(topicId);
const toggleExpand = (topicId: string) => {
  const idx = expandedTopics.value.indexOf(topicId);
  if (idx > -1) {
    expandedTopics.value.splice(idx, 1);
    clearReportPoll(topicId);
  } else {
    expandedTopics.value.push(topicId);
    if (!reportMap[topicId] && !reportLoadingMap[topicId]) {
      fetchReport(topicId);
    }
  }
};

const clearReportPoll = (topicId: string) => {
  const timer = reportPollTimers.get(topicId);
  if (timer !== undefined) {
    window.clearTimeout(timer);
    reportPollTimers.delete(topicId);
  }
};

const scheduleReportPoll = (topicId: string) => {
  clearReportPoll(topicId);
  const timer = window.setTimeout(() => {
    pollReportStatus(topicId);
  }, 2000);
  reportPollTimers.set(topicId, timer);
};

const pollReportStatus = async (topicId: string) => {
  try {
    const { data } = await getTopicReportTask(topicId);
    if (data.status === 'success' && data.report) {
      reportMap[topicId] = data.report;
      reportLoadingMap[topicId] = false;
      clearReportPoll(topicId);
      return;
    }
    if (data.status === 'failed') {
      reportErrorMap[topicId] = data.error || '报告生成失败';
      reportLoadingMap[topicId] = false;
      clearReportPoll(topicId);
      return;
    }
    if (data.status === 'missing') {
      await fetchReport(topicId, true);
      return;
    }
  } catch (e) {
    reportErrorMap[topicId] = '报告状态获取失败';
    reportLoadingMap[topicId] = false;
    clearReportPoll(topicId);
    return;
  }
  scheduleReportPoll(topicId);
};

const fetchReport = async (topicId: string, force = false) => {
  if (reportLoadingMap[topicId] && !force) return;
  reportLoadingMap[topicId] = true;
  reportErrorMap[topicId] = null;
  try {
    const { data } = await startTopicReport(topicId, force);
    if (data.status === 'success' && data.report) {
      reportMap[topicId] = data.report;
      reportLoadingMap[topicId] = false;
      clearReportPoll(topicId);
      return;
    }
    if (data.status === 'failed') {
      reportErrorMap[topicId] = data.error || '报告生成失败';
      reportLoadingMap[topicId] = false;
      clearReportPoll(topicId);
      return;
    }
    scheduleReportPoll(topicId);
  } catch (e) {
    reportErrorMap[topicId] = '加载报告失败';
    reportLoadingMap[topicId] = false;
    clearReportPoll(topicId);
  }
};

const goTopicReport = (topicId: string) => {
  router.push({ name: 'TopicDetail', params: { topicId }, query: { tab: 'report' } });
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

watch([keyword, typeFilter, sortOrder], () => {
  currentPage.value = 1;
});

onMounted(() => {
  loadTopics();
});

onBeforeUnmount(() => {
  reportPollTimers.forEach((timer, topicId) => {
    window.clearTimeout(timer);
    reportPollTimers.delete(topicId);
  });
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
