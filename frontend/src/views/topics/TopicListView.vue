<template>
  <div class="space-y-5">
    <!-- 顶部渐变区域：标题 + 搜索 + 新建 -->
    <section
      class="overflow-hidden rounded-2xl bg-gradient-to-r from-[#E3F0FF] via-[#EDEBFF] to-[#E5FBFF] px-6 py-5 shadow-sm"
    >
      <div
        class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
      >
        <div class="space-y-3">
          <div
            class="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-[11px] font-medium text-sky-700"
          >
            <span class="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span>课题工作台 · B 站内容研究</span>
          </div>
          <div>
            <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">
              课题工作台
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              管理你的 B 站分析课题，快速进入会话分析与报告生成。
            </p>
          </div>
        </div>

        <div class="flex flex-col items-stretch gap-2 md:w-80">
          <el-input
            v-model="searchKeyword"
            size="small"
            placeholder="搜索课题名称或描述"
            clearable
            class="rounded-full bg-white/90"
            @clear="handleFilterChange"
            @input="handleFilterChange"
          >
            <template #prefix>
              <el-icon><i-ep-search /></el-icon>
            </template>
          </el-input>
          <div class="flex items-center justify-end gap-2">
            <div class="text-[11px] text-slate-500">
              共
              <span class="font-semibold text-slate-800">
                {{ totalTopics }}
              </span>
              个课题
            </div>
            <el-button
              type="primary"
              size="small"
              round
              @click="openCreateDialog"
            >
              新建课题
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 筛选栏 -->
    <section>
      <el-card
        shadow="never"
        class="!rounded-2xl !border-none !bg-white"
      >
        <div
          class="flex flex-wrap items-center gap-3 text-xs text-slate-600"
        >
          <span class="text-slate-500">筛选条件</span>
          <el-select
            v-model="filters.topicType"
            size="small"
            clearable
            placeholder="课题类型"
            class="min-w-[140px]"
            @change="handleFilterChange"
          >
            <el-option
              v-for="item in topicTypeOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>

          <el-button
            text
            type="primary"
            size="small"
            round
            @click="resetFilters"
          >
            重置筛选
          </el-button>

          <el-divider direction="vertical" />
          <span class="text-slate-500">
            当前显示第 {{ topicPage }} 页，共 {{ totalTopics }} 个课题
          </span>
        </div>
      </el-card>
    </section>

    <!-- 课题卡片列表 -->
    <section>
      <el-card
        shadow="never"
        class="!rounded-2xl !border-none !bg-transparent !p-0"
      >
        <el-skeleton v-if="loading" animated :rows="4" />

        <template v-else>
          <el-empty
            v-if="!topics.length"
            description="暂时还没有课题"
          >
            <el-button
              type="primary"
              size="small"
              round
              @click="openCreateDialog"
            >
              新建第一个课题
            </el-button>
          </el-empty>

          <div
            v-else
            class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
          >
            <article
              v-for="topic in topics"
              :key="topic.topic_id"
              class="group relative flex flex-col overflow-hidden rounded-[14px] border border-slate-200 bg-white/95 p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-sky-300 hover:shadow-md cursor-pointer"
              @click="goTopicDetail(topic.topic_id)"
            >
              <!-- 顶部渐变条 + 类型标签 -->
              <div class="mb-3 flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span
                    class="h-1 w-10 rounded-full bg-gradient-to-r from-sky-400 via-indigo-400 to-cyan-400"
                  />
                  <span
                    class="rounded-full bg-sky-50 px-2 py-0.5 text-[11px] font-medium text-sky-700"
                  >
                    {{ topic.topic_type || '未分类' }}
                  </span>
                </div>
                <span class="text-[11px] text-slate-400">
                  最近更新：{{ formatTime(topic.updated_at) }}
                </span>
              </div>

              <!-- 标题 + 描述 -->
              <div class="flex-1 min-w-0">
                <h3
                  class="truncate text-base font-semibold text-slate-900 group-hover:text-sky-700"
                >
                  {{ topic.name }}
                </h3>
                <p class="mt-1 text-sm text-slate-500 line-clamp-2">
                  {{
                    topic.description ||
                    '暂无课题描述，可在编辑中补充研究范围与目的。'
                  }}
                </p>
              </div>

              <!-- 底部统计 + 操作 -->
              <div class="mt-3 flex items-end justify-between gap-2">
                <div
                  class="flex flex-wrap items-center gap-2 text-[11px] text-slate-500"
                >
                  <span
                    class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full bg-sky-400" />
                    创建：{{ formatTime(topic.created_at) }}
                  </span>
                  <span
                    v-if="topic.conversations_count !== undefined"
                    class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    会话：{{ topic.conversations_count }}
                  </span>
                  <span
                    v-if="topic.datasets_count !== undefined"
                    class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                    数据集：{{ topic.datasets_count }}
                  </span>
                  <span
                    v-if="topic.reports_count !== undefined"
                    class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full bg-violet-400" />
                    报告：{{ topic.reports_count }}
                  </span>
                </div>

                <el-dropdown
                  @click.stop
                  @command="(cmd: string) => handleRowCommand(cmd, topic)"
                >
                  <el-button text size="small" round>
                    操作
                    <el-icon class="el-icon--right">
                      <i-ep-arrow-down />
                    </el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="open">
                        打开课题
                      </el-dropdown-item>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item divided command="delete">
                        <span class="text-orange-500">删除</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </article>
          </div>

          <div class="mt-4 flex justify-end">
            <el-pagination
              v-model:current-page="topicPage"
              v-model:page-size="topicPageSize"
              background
              layout="prev, pager, next, sizes, total"
              :total="totalTopics"
              :page-sizes="[6, 12, 18, 24]"
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
            />
          </div>
        </template>
      </el-card>
    </section>

    <!-- 新建 / 编辑课题弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTopic ? '编辑课题' : '新建课题'"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        size="small"
        class="pt-2"
      >
        <el-form-item label="课题名称" prop="name">
          <el-input
            v-model="form.name"
            maxlength="60"
            show-word-limit
            placeholder="例如：成都 3 天 2 夜旅游攻略研究"
          />
        </el-form-item>
        <el-form-item label="课题类型" prop="topic_type">
          <el-input
            v-model="form.topic_type"
            maxlength="30"
            show-word-limit
            placeholder="例如：旅游攻略、美食测评、数码评测"
          />
        </el-form-item>
        <el-form-item label="课题描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="300"
            show-word-limit
            placeholder="简要说明这个课题的研究范围与目的，例如：围绕 B 站视频评论分析成都旅游吃喝玩乐的口碑与情绪走势。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSubmit">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";
import { listTopics, createTopic, updateTopic, deleteTopic } from '@/api/topics';
import type { TopicDetail, TopicListItem } from '@/types/api';
import type { TopicCreatePayload } from '@/api/topics';

const router = useRouter();

const loading = ref(false);
const topics = ref<TopicListItem[]>([]);
const totalTopics = ref(0);

const searchKeyword = ref('');
const topicTypeOptions = computed(() => {
  const set = new Set<string>();
  topics.value.forEach((t) => {
    if (t.topic_type) {
      set.add(t.topic_type);
    }
  });
  return ['全部', ...Array.from(set)];
});
const filters = reactive({
  topicType: '',
});
const topicPage = ref(1);
const topicPageSize = ref(12);

const dialogVisible = ref(false);
const saving = ref(false);
const editingTopic = ref<TopicDetail | null>(null);

const formRef = ref<FormInstance>();
const form = reactive({
  name: '',
  topic_type: '',
  description: '',
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入课题名称', trigger: 'blur' }],
  topic_type: [{ required: true, message: '请输入课题类型', trigger: 'blur' }],
};

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const fetchTopics = async () => {
  loading.value = true;
  try {
    const { data } = await listTopics({
      limit: topicPageSize.value,
      offset: (topicPage.value - 1) * topicPageSize.value,
      keyword: searchKeyword.value || undefined,
      topic_type:
        filters.topicType && filters.topicType !== '全部'
          ? filters.topicType
          : undefined,
    });
    topics.value = data.items;
    totalTopics.value = data.total;
  } catch (e) {
    ElMessage.error('获取课题列表失败');
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  topicPage.value = 1;
  fetchTopics();
};

const resetFilters = () => {
  filters.topicType = '';
  searchKeyword.value = '';
  topicPage.value = 1;
  fetchTopics();
};

const openCreateDialog = () => {
  editingTopic.value = null;
  form.name = '';
  form.topic_type = '';
  form.description = '';
  dialogVisible.value = true;
};

const openEditDialog = (topic: TopicDetail | TopicListItem) => {
  editingTopic.value = topic as TopicDetail;
  form.name = topic.name;
  form.topic_type = topic.topic_type || '';
  form.description = topic.description || '';
  dialogVisible.value = true;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editingTopic.value) {
        const { data } = await updateTopic(editingTopic.value.topic_id, form);
        topics.value = topics.value.map((t) => (t.topic_id === data.topic_id ? data : t));
        ElMessage.success('课题更新成功');
      } else {
        const payload: TopicCreatePayload = {
          name: form.name,
          topic_type: form.topic_type,
          description: form.description || '',
        };
        const { data } = await createTopic(payload);
        topics.value.unshift(data);
        totalTopics.value += 1;
        ElMessage.success('课题创建成功');
      }
      dialogVisible.value = false;
    } catch (e) {
      ElMessage.error('保存失败，请稍后重试');
    } finally {
      saving.value = false;
    }
  });
};

const goTopicDetail = (topicId: string) => {
  router.push({ name: 'TopicDetail', params: { topicId } });
};

const handleRowCommand = (command: string, topic: TopicListItem) => {
  if (command === 'open') {
    goTopicDetail(topic.topic_id);
  } else if (command === 'edit') {
    openEditDialog(topic);
  } else if (command === 'delete') {
    handleDelete(topic.topic_id);
  }
};

const handleDelete = (topicId: string) => {
  ElMessageBox.confirm('确定要删除该课题吗？删除后将无法恢复。', '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
    .then(async () => {
      await deleteTopic(topicId);
      ElMessage.success('删除成功');
      topics.value = topics.value.filter((t) => t.topic_id !== topicId);
      totalTopics.value = Math.max(totalTopics.value - 1, 0);
    })
    .catch(() => {});
};

const handlePageChange = () => {
  fetchTopics();
};

const handleSizeChange = () => {
  topicPage.value = 1;
  fetchTopics();
};

onMounted(() => {
  fetchTopics();
});
</script>
