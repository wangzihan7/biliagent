<template>
  <div class="space-y-6">
    <div v-if="summaryBlocks.length" class="grid gap-4 md:grid-cols-2">
      <section
        v-for="block in summaryBlocks"
        :key="block.title"
        class="rounded-2xl border border-slate-100 bg-slate-50/80 p-4 max-h-[320px] overflow-auto"
      >
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {{ block.title }}
        </p>
        <div
          class="mt-2 text-sm leading-relaxed text-slate-700 markdown-body"
          v-html="renderMarkdown(block.content)"
        />
        <div v-if="block.content.length > 400" class="mt-2 text-right">
          <el-button type="primary" link size="small" @click="showDetail(block)">
            查看详情
          </el-button>
        </div>
      </section>
    </div>

    <el-dialog
      v-model="detailVisible"
      :title="detailBlock?.title || '详情'"
      width="720px"
      destroy-on-close
    >
      <div class="markdown-body text-sm leading-relaxed">
        <div v-html="detailBlock ? renderMarkdown(detailBlock.content) : ''" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <div v-if="totalsList.length" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="item in totalsList"
        :key="item.label"
        class="rounded-2xl border border-slate-100 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"
      >
        <p class="text-xs text-slate-500">{{ item.label }}</p>
        <p class="mt-2 text-2xl font-semibold text-slate-900">
          {{ formatNumber(item.value) }}
          <span class="ml-1 text-xs font-normal text-slate-400">{{ item.unit }}</span>
        </p>
        <p v-if="item.hint" class="mt-1 text-[11px] text-slate-400">
          {{ item.hint }}
        </p>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm min-h-[300px]">
        <header class="mb-2 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-slate-800">情感分布</h4>
            <p class="text-xs text-slate-500">对评论/弹幕情绪的占比情况</p>
          </div>
        </header>
        <div v-if="sentimentAvailable" ref="sentimentChartRef" class="h-64" />
        <el-empty v-else description="暂无情感分析数据" :image-size="80" />
      </section>

      <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm min-h-[300px]">
        <header class="mb-2 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-slate-800">讨论趋势</h4>
            <p class="text-xs text-slate-500">按日期统计的评论/弹幕量</p>
          </div>
        </header>
        <div v-if="trendAvailable" ref="trendChartRef" class="h-64" />
        <el-empty v-else description="暂无趋势统计" :image-size="80" />
      </section>

      <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm min-h-[300px]">
        <header class="mb-2 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-slate-800">热门标签</h4>
            <p class="text-xs text-slate-500">高频出现的语义标签</p>
          </div>
        </header>
        <div v-if="topTagsWithValues.length" ref="tagsChartRef" class="h-64" />
        <template v-else>
          <ul v-if="topTagsList.length" class="space-y-1 text-sm text-slate-600">
            <li
              v-for="tag in topTagsList"
              :key="tag"
              class="rounded-full bg-slate-50 px-3 py-1 text-xs inline-block mr-2 mb-2"
            >
              {{ tag }}
            </li>
          </ul>
          <el-empty v-else description="暂无标签数据" :image-size="80" />
        </template>
      </section>

      <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm min-h-[300px]">
        <header class="mb-2 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-slate-800">高频关键词</h4>
            <p class="text-xs text-slate-500">模型总结的核心关键词</p>
          </div>
        </header>
        <div v-if="topKeywordsWithValues.length" ref="keywordsChartRef" class="h-64" />
        <template v-else>
          <ul v-if="topKeywordsList.length" class="space-y-1 text-sm text-slate-600">
            <li
              v-for="keyword in topKeywordsList"
              :key="keyword"
              class="rounded-full bg-slate-50 px-3 py-1 text-xs inline-block mr-2 mb-2"
            >
              {{ keyword }}
            </li>
          </ul>
          <el-empty v-else description="暂无关键词数据" :image-size="80" />
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  watch,
} from 'vue';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import type { ECharts } from 'echarts';
import type { TopicReport, TopicReportLabelValueItem } from '@/types/api';

const props = defineProps<{
  report: TopicReport;
}>();

type ChartKey = 'sentiment' | 'trend' | 'tags' | 'keywords';

const sentimentChartRef = ref<HTMLDivElement | null>(null);
const trendChartRef = ref<HTMLDivElement | null>(null);
const tagsChartRef = ref<HTMLDivElement | null>(null);
const keywordsChartRef = ref<HTMLDivElement | null>(null);

const chartInstances: Record<ChartKey, ECharts | null> = {
  sentiment: null,
  trend: null,
  tags: null,
  keywords: null,
};

const vueInstance = getCurrentInstance();
const echarts = vueInstance?.appContext.config.globalProperties.$echarts as
  | typeof import('echarts')
  | undefined;

const formatNumber = (value?: number) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '--';
  return Number(value).toLocaleString();
};

const summaryBlocks = computed(() => {
  const blocks: { title: string; content: string }[] = [];
  if (props.report.summary) {
    blocks.push({ title: '统计摘要', content: props.report.summary });
  }
  if (props.report.llm_summary) {
    blocks.push({ title: '模型洞察', content: props.report.llm_summary });
  }
  return blocks;
});

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

const detailVisible = ref(false);
const detailBlock = ref<{ title: string; content: string } | null>(null);
const showDetail = (block: { title: string; content: string }) => {
  detailBlock.value = block;
  detailVisible.value = true;
};

interface TotalCardItem {
  label: string;
  value?: number;
  unit: string;
  hint?: string;
}

const totalsList = computed<TotalCardItem[]>(() => {
  if (!props.report.totals) return [];
  return [
    { label: '关联数据集', value: props.report.totals.datasets, unit: '个' },
    { label: '覆盖视频数', value: props.report.totals.videos, unit: '条' },
    { label: '评论量', value: props.report.totals.comments, unit: '条' },
    { label: '弹幕量', value: props.report.totals.danmaku, unit: '条' },
  ].filter((item) => item.value !== undefined);
});

const normalizeLabelValue = (
  list?: (string | TopicReportLabelValueItem)[],
): TopicReportLabelValueItem[] => {
  if (!list?.length) return [];
  return list
    .map((item) => {
      if (typeof item === 'string') return null;
      if (item?.name && item?.value !== undefined) {
        return { name: item.name, value: Number(item.value) };
      }
      return null;
    })
    .filter((item): item is TopicReportLabelValueItem => !!item);
};

const extractNameList = (list?: (string | TopicReportLabelValueItem)[]) => {
  if (!list?.length) return [];
  return list
    .map((item) => (typeof item === 'string' ? item : item?.name))
    .filter((item): item is string => !!item);
};

const sentimentData = computed<TopicReportLabelValueItem[]>(() => {
  if (props.report.charts?.sentiment?.length) {
    return props.report.charts.sentiment;
  }
  if (props.report.sentiment) {
    return Object.entries(props.report.sentiment).map(([name, value]) => ({
      name,
      value,
    }));
  }
  return [];
});

const trendData = computed(() => {
  if (props.report.charts?.trend?.length) return props.report.charts.trend;
  return props.report.trend || [];
});

const topTagsWithValues = computed(() => {
  if (props.report.charts?.top_tags?.length) return props.report.charts.top_tags;
  return normalizeLabelValue(props.report.top_tags);
});

const topKeywordsWithValues = computed(() => {
  if (props.report.charts?.top_keywords?.length) {
    return props.report.charts.top_keywords;
  }
  return normalizeLabelValue(props.report.top_keywords);
});

const topTagsList = computed(() => extractNameList(props.report.top_tags));
const topKeywordsList = computed(() => extractNameList(props.report.top_keywords));

const sentimentAvailable = computed(() => sentimentData.value.length > 0);
const trendAvailable = computed(() => trendData.value.length > 0);

const disposeChart = (key: ChartKey) => {
  if (chartInstances[key]) {
    chartInstances[key]?.dispose();
    chartInstances[key] = null;
  }
};

const ensureChart = (key: ChartKey, el: HTMLDivElement) => {
  if (!echarts) return null;
  if (!chartInstances[key]) {
    chartInstances[key] = echarts.init(el);
  }
  return chartInstances[key];
};

const renderSentimentChart = () => {
  const data = sentimentData.value;
  const el = sentimentChartRef.value;
  if (!data.length || !el || !echarts) {
    disposeChart('sentiment');
    return;
  }
  const chart = ensureChart('sentiment', el);
  chart?.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle' },
    series: [
      {
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '45%'],
        data,
        label: { formatter: '{b}: {d}%' },
      },
    ],
  });
};

const renderTrendChart = () => {
  const data = trendData.value;
  const el = trendChartRef.value;
  if (!data.length || !el || !echarts) {
    disposeChart('trend');
    return;
  }

  const commentValues = data.map((item) =>
    item.comment_count ?? item.comments ?? null,
  );
  const danmakuValues = data.map((item) =>
    item.danmaku_count ?? item.danmaku ?? null,
  );
  const fallbackValues = data.map(
    (item) => item.count ?? item.comment_count ?? item.danmaku_count ?? 0,
  );

  const series = [];
  if (commentValues.some((v) => v !== null)) {
    series.push({
      name: '评论量',
      type: 'line',
      smooth: true,
      data: data.map((item, idx) => [item.date, commentValues[idx] ?? 0]),
      areaStyle: { opacity: 0.05 },
    });
  }
  if (danmakuValues.some((v) => v !== null)) {
    series.push({
      name: '弹幕量',
      type: 'line',
      smooth: true,
      data: data.map((item, idx) => [item.date, danmakuValues[idx] ?? 0]),
      areaStyle: { opacity: 0.05 },
    });
  }
  if (!series.length) {
    series.push({
      name: '讨论量',
      type: 'line',
      smooth: true,
      data: data.map((item, idx) => [item.date, fallbackValues[idx]]),
      areaStyle: { opacity: 0.05 },
    });
  }

  const chart = ensureChart('trend', el);
  chart?.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 45, right: 16, top: 36, bottom: 32 },
    xAxis: { type: 'category', boundaryGap: false, data: data.map((item) => item.date) },
    yAxis: { type: 'value' },
    series,
  });
};

const renderBarChart = (key: 'tags' | 'keywords') => {
  const el = key === 'tags' ? tagsChartRef.value : keywordsChartRef.value;
  const data =
    key === 'tags'
      ? topTagsWithValues.value
      : topKeywordsWithValues.value;
  if (!data.length || !el || !echarts) {
    disposeChart(key);
    return;
  }
  const sorted = [...data].sort((a, b) => b.value - a.value);
  const chart = ensureChart(key, el);
  chart?.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 16, top: 20, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
    yAxis: {
      type: 'category',
      inverse: true,
      data: sorted.map((item) => item.name),
      axisLabel: { color: '#475569' },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((item) => item.value),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 8, 8, 0],
          color: key === 'tags' ? '#38bdf8' : '#a855f7',
        },
      },
    ],
  });
};

const renderCharts = () => {
  renderSentimentChart();
  renderTrendChart();
  renderBarChart('tags');
  renderBarChart('keywords');
};

const handleResize = () => {
  (Object.values(chartInstances) as (ECharts | null)[]).forEach((instance) => {
    instance?.resize();
  });
};

onMounted(() => {
  nextTick(() => renderCharts());
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  (Object.keys(chartInstances) as ChartKey[]).forEach((key) => disposeChart(key));
});

watch(
  () => props.report,
  () => {
    nextTick(() => renderCharts());
  },
  { deep: true },
);
</script>
