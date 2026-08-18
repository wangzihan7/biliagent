<template>
  <div class="chat-page flex gap-4 h-full">
    <section class="chat-sidebar w-72 flex-shrink-0">
      <el-card
        shadow="never"
        class="sidebar-card !rounded-2xl !border-none !bg-white flex flex-col"
      >
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-slate-900">我的会话</h3>
          <el-button type="primary" size="small" round @click="handleCreateConversation">
            新建会话
          </el-button>
        </div>

        <el-input
          v-model="keyword"
          size="small"
          placeholder="搜索会话"
          class="mb-3"
          clearable
        >
          <template #prefix>
            <el-icon><i-ep-search /></el-icon>
          </template>
        </el-input>

        <div class="sidebar-list flex-1 space-y-1">
          <el-skeleton v-if="loadingConversations" :rows="4" animated />
          <template v-else>
            <el-empty
              v-if="!filteredConversations.length"
              :image-size="80"
              description="暂无会话"
            />
            <div
              v-else
              v-for="conv in filteredConversations"
              :key="conv.conversation_id"
              class="group flex items-center justify-between gap-2 rounded-xl px-3 py-2 text-xs transition-colors"
              :class="
                conv.conversation_id === currentConversationId
                  ? 'bg-sky-50 text-sky-700'
                  : 'hover:bg-slate-100 text-slate-600'
              "
            >
              <div
                class="min-w-0 flex-1 cursor-pointer"
                @click="selectConversation(conv.conversation_id)"
              >
                <p class="font-medium truncate">
                  {{ conv.conversation_name || '未命名会话' }}
                </p>
                <p class="mt-1 text-[10px] opacity-70">
                  更新：{{ formatTime(conv.update_time) }}
                </p>
              </div>

              <el-dropdown
                trigger="click"
                @command="(cmd: string) => handleSidebarCommand(cmd, conv.conversation_id)"
                @click.stop
              >
                <el-button
                  text
                  circle
                  size="small"
                  class="!opacity-0 group-hover:!opacity-100 transition-opacity"
                >
                  <el-icon><i-ep-more-filled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">
                      <el-icon><i-ep-edit /></el-icon>
                      <span class="ml-1">重命名</span>
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><i-ep-delete /></el-icon>
                      <span class="ml-1">删除</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </div>
      </el-card>
    </section>

    <section class="flex-1 flex flex-col">
      <el-card
        shadow="never"
        class="!rounded-2xl !border-none !bg-white flex-1 flex flex-col"
      >
        <header class="mb-3 flex items-center justify-between">
          <div>
            <h3 class="text-base font-semibold text-slate-900">
              {{ currentConversationTitle }}
            </h3>
            <p class="mt-0.5 text-xs text-slate-500">
              结合课题数据集对 B 站内容进行智能分析。
            </p>
          </div>
          <div class="flex items-center gap-3 text-xs text-slate-500">
            <el-select
              v-model="selectedDatasetIds"
              size="small"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="2"
              class="min-w-[200px]"
              placeholder="选择数据集"
            >
              <el-option
                v-for="ds in datasets"
                :key="ds.dataset_id"
                :label="ds.name"
                :value="ds.dataset_id"
              />
            </el-select>
          </div>
        </header>

        <div
          ref="messageListRef"
          class="message-list flex-1 overflow-y-auto mb-3 space-y-3 pr-1"
          @scroll="handleScroll"
        >
          <el-skeleton v-if="loadingMessages" :rows="4" animated />
          <template v-else>
            <div
              v-for="msg in messages"
              :key="msg.message_id"
              class="flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[72%] rounded-2xl px-3 py-2 text-sm shadow-sm"
                :class="
                  msg.role === 'user'
                    ? 'bg-sky-500 text-white rounded-br-sm'
                    : 'bg-slate-50 text-slate-800 rounded-bl-sm'
                "
              >
                <p v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.content }}</p>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)" />
          <div
            v-if="msg.meta_data?.metrics && msg.role === 'assistant'"
            class="mt-1 text-[10px] text-slate-400 flex gap-2"
          >
            <span>耗时：{{ msg.meta_data.metrics.latency_ms }}ms</span>
            <span>tokens：{{ msg.meta_data.metrics.total_tokens_est }}</span>
          </div>
          <div v-if="msg.role === 'assistant'" class="mt-2 flex justify-end">
                  <el-tooltip
                    :content="msg.meta_data?.is_important ? '取消关键回答' : '设为关键回答'"
                    placement="top"
                  >
                    <button
                      class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] transition-colors disabled:opacity-70"
                      :class="
                        msg.meta_data?.is_important
                          ? 'border-amber-200 bg-amber-50 text-amber-600'
                          : 'border-slate-200 text-slate-400 hover:text-slate-600'
                      "
                      :disabled="importantLoading[msg.message_id] || (msg.message_id || '').startsWith('local-')"
                      @click.stop="toggleImportant(msg)"
                    >
                      <el-icon size="12">
                        <i-ep-star-filled v-if="msg.meta_data?.is_important" />
                        <i-ep-star v-else />
                      </el-icon>
                      <span>
                        {{ msg.meta_data?.is_important ? '已标记' : '设为关键回答' }}
                      </span>
                    </button>
                  </el-tooltip>
                </div>
              </div>
            </div>

            <div v-if="isStreaming" class="flex justify-start">
              <div
                class="max-w-[72%] rounded-2xl rounded-bl-sm bg-slate-50 px-3 py-2 text-sm shadow-sm"
              >
                <div class="markdown-body" v-html="renderMarkdown(answerText)" />
                <span v-if="isStreaming" class="animate-pulse text-slate-400">▋</span>
          <div v-if="metrics" class="mt-1 text-[10px] text-slate-400 flex gap-2">
            <span>耗时：{{ metrics.latency_ms }}ms</span>
            <span>tokens：{{ metrics.total_tokens_est }}</span>
          </div>
        </div>
      </div>
          </template>
        </div>

        <footer class="chat-input border-t border-slate-200 pt-2 mt-auto">
          <el-form @submit.prevent>
            <el-form-item>
              <el-input
                v-model="input"
                type="textarea"
                :rows="3"
                placeholder="围绕 B 站内容提出你的问题，例如：帮我总结这个课题下最常被提到的美食建议。"
                @keydown="handleKeydown"
              />
            </el-form-item>
            <div class="flex items-center justify-between">
              <div class="flex flex-col text-[11px] text-slate-400">
                <div>回车发送，Shift+Enter 换行。</div>
                <div v-if="showDatasetWarning" class="mt-1 text-rose-500">
                  请先选择数据集后再发送。
                </div>
              </div>
              <el-button
                type="primary"
                round
                :loading="isStreaming"
                :disabled="!canSend"
                @click="handleSend"
              >
                发送
              </el-button>
            </div>
          </el-form>
        </footer>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import {
  listUserConversations,
  createConversation,
  getMessages,
  markMessageImportant,
  deleteConversation,
  updateConversation,
} from '@/api/conversations';
import { listDatasets } from '@/api/datasets';
import type { Conversation, Message, DatasetSummary } from '@/types/api';
import { useChatStream } from '@/composables/useChatStream';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const loadingConversations = ref(false);
const loadingMessages = ref(false);

const conversations = ref<Conversation[]>([]);
const messages = ref<Message[]>([]);
const importantLoading = ref<Record<string, boolean>>({});

const datasets = ref<DatasetSummary[]>([]);
const selectedDatasetIds = ref<string[]>([]);

const currentConversationId = ref<string | null>(
  (route.params.conversationId as string) || null,
);

const input = ref('');
const keyword = ref('');
const scrollToken = ref(0);
const shouldRefreshAfterStream = ref(false);

const {
  answerText,
  metrics,
  isStreaming,
  startChat,
} = useChatStream();

const filteredConversations = computed(() => {
  if (!keyword.value) return conversations.value;
  const kw = keyword.value.toLowerCase();
  return conversations.value.filter((c) =>
    (c.conversation_name || '').toLowerCase().includes(kw),
  );
});

const currentConversationTitle = computed(() => {
  const id = currentConversationId.value;
  if (!id) return '请选择或新建会话';
  const conv = conversations.value.find((c) => c.conversation_id === id);
  return conv?.conversation_name || '未命名会话';
});

const canSend = computed(() => {
  if (!input.value.trim()) return false;
  if (!currentConversationId.value) return false;
  if (!selectedDatasetIds.value.length) return false;
  return true;
});

const showDatasetWarning = computed(() => {
  if (!input.value.trim()) return false;
  if (!currentConversationId.value) return false;
  return !selectedDatasetIds.value.length;
});

const formatTime = (val?: string) => {
  if (!val) return '-';
  return val.replace('T', ' ').split('.')[0];
};

const bumpScroll = () => {
  scrollToken.value += 1;
};

const md = new MarkdownIt({
  linkify: true,
  breaks: true,
});

// 统一为生成的链接添加新窗口和安全属性
const defaultLinkOpen = md.renderer.rules.link_open || function (tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const aIndex = tokens[idx].attrIndex('target');
  if (aIndex < 0) {
    tokens[idx].attrPush(['target', '_blank']);
  } else {
    tokens[idx].attrs![aIndex][1] = '_blank';
  }
  tokens[idx].attrPush(['rel', 'noopener noreferrer']);
  return defaultLinkOpen(tokens, idx, options, env, self);
};

const renderMarkdown = (text: string) => {
  return DOMPurify.sanitize(md.render(text || ''), {
    ADD_ATTR: ['target', 'rel'],
  });
};

const messageListRef = ref<HTMLDivElement | null>(null);
const isAtBottom = ref(true);

const scrollToBottom = (force = false) => {
  if (!force && !isAtBottom.value) return;
  nextTick(() => {
    const el = messageListRef.value;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  });
};

const handleScroll = () => {
  const el = messageListRef.value;
  if (!el) return;
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
  isAtBottom.value = distanceFromBottom < 40;
};

const fetchConversations = async () => {
  if (!auth.userId) return;
  loadingConversations.value = true;
  try {
    const { data } = await listUserConversations(auth.userId, { limit: 50 });
    conversations.value = data;
    if (!currentConversationId.value && data.length) {
      const firstConversation = data[0];
      if (firstConversation?.conversation_id) {
        selectConversation(firstConversation.conversation_id);
      }
    }
  } catch (e) {
    ElMessage.error('获取会话列表失败');
  } finally {
    loadingConversations.value = false;
  }
};

const fetchMessages = async () => {
  const id = currentConversationId.value;
  if (!id) return;
  loadingMessages.value = true;
  try {
    const { data } = await getMessages(id, { limit: 50 });
    messages.value = data;
    bumpScroll();
  } catch (e) {
    ElMessage.error('获取消息历史失败');
  } finally {
    loadingMessages.value = false;
  }
};

const fetchDatasets = async () => {
  try {
    const { data } = await listDatasets({ limit: 100, offset: 0 });
    datasets.value = data.items;
  } catch {
    // 忽略加载失败，聊天仍可继续
  }
};

const selectConversation = (conversationId: string) => {
  if (conversationId === currentConversationId.value) return;
  currentConversationId.value = conversationId;
  router.replace({ name: 'Chat', params: { conversationId } });
  fetchMessages();
};

const handleCreateConversation = async () => {
  if (!auth.userId) {
    ElMessage.error('请先登录');
    return;
  }
  try {
    const { data } = await createConversation({
      user_id: auth.userId,
      conversation_name: '新的分析会话',
    });
    conversations.value.unshift(data);
    selectConversation(data.conversation_id);
  } catch (e) {
    ElMessage.error('创建会话失败');
  }
};

const handleDeleteConversation = async (conversationId: string) => {
  if (!conversationId) return;
  const target = conversations.value.find((c) => c.conversation_id === conversationId);
  const name = target?.conversation_name || '该会话';
  if (!window.confirm(`确认删除「${name}」？该操作会删除会话消息和课题绑定关系。`)) {
    return;
  }
  try {
    await deleteConversation(conversationId);
    conversations.value = conversations.value.filter(
      (c) => c.conversation_id !== conversationId,
    );
    if (currentConversationId.value === conversationId) {
      const first = conversations.value[0];
      currentConversationId.value = first ? first.conversation_id : null;
      messages.value = [];
      if (first?.conversation_id) {
        router.replace({ name: 'Chat', params: { conversationId: first.conversation_id } });
        fetchMessages();
      } else {
        router.replace({ name: 'Chat' });
      }
    }
    ElMessage.success('会话已删除');
  } catch (e) {
    ElMessage.error('删除会话失败');
  }
};

const handleRenameConversation = async (conversationId: string) => {
  const target = conversations.value.find((c) => c.conversation_id === conversationId);
  if (!target) return;
  try {
    const { value } = await ElMessageBox.prompt('请输入新的会话名称', '重命名会话', {
      inputValue: target.conversation_name || '',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：成都旅游攻略',
      inputValidator: (val: string) => {
        const name = (val || '').trim();
        if (!name) return '会话名称不能为空';
        if (name.length > 200) return '会话名称过长';
        return true;
      },
    });
    const newName = (value || '').trim();
    if (!newName || newName === target.conversation_name) return;

    const { data } = await updateConversation(conversationId, { conversation_name: newName });
    // 更新本地列表，并把更新后的会话置顶（update_time 会更大）
    conversations.value = [
      data,
      ...conversations.value.filter((c) => c.conversation_id !== conversationId),
    ];
    ElMessage.success('会话名称已更新');
  } catch (e: any) {
    // 用户取消不提示错误
    if (e === 'cancel' || e?.message === 'cancel') return;
  }
};

const handleSidebarCommand = (command: string, conversationId: string) => {
  if (command === 'rename') {
    handleRenameConversation(conversationId);
  } else if (command === 'delete') {
    handleDeleteConversation(conversationId);
  }
};

const setImportantLoading = (messageId: string, value: boolean) => {
  importantLoading.value = {
    ...importantLoading.value,
    [messageId]: value,
  };
};

const toggleImportant = async (msg: Message) => {
  const messageId = msg.message_id;
  if (!messageId) return;
  if (messageId.startsWith('local-')) {
    ElMessage.warning('消息正在保存，请稍后再试');
    // 尝试刷新一次，拿到后端真实 message_id
    fetchMessages();
    return;
  }
  const current = !!msg.meta_data?.is_important;
  setImportantLoading(messageId, true);
  try {
    await markMessageImportant(messageId, !current);
    const meta = msg.meta_data ? { ...msg.meta_data } : {};
    meta.is_important = !current;
    msg.meta_data = meta;
    messages.value = [...messages.value];
    ElMessage.success(!current ? '已设为关键回答' : '已取消关键回答');
  } catch (e) {
    ElMessage.error('更新关键回答状态失败');
  } finally {
    setImportantLoading(messageId, false);
  }
};

const handleSend = async () => {
  const convId = currentConversationId.value;
  const content = input.value.trim();
  if (!content || !convId || !auth.userId || !canSend.value) return;

  messages.value.push({
    message_id: `local-${Date.now()}`,
    conversation_id: convId,
    role: 'user',
    content,
    create_time: new Date().toISOString(),
  } as Message);
  bumpScroll();

  input.value = '';

  try {
    await startChat(
      {
        user_id: auth.userId,
        conversation_id: convId,
        query: content,
        dataset_ids: selectedDatasetIds.value.length
          ? selectedDatasetIds.value
          : undefined,
      },
      {
        onDone() {
          shouldRefreshAfterStream.value = true;
        },
      },
    );
  } catch (e) {
    ElMessage.error('发送消息失败');
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key !== 'Enter') return;
  if (event.shiftKey) return;
  event.preventDefault();
  if (!canSend.value) return;
  handleSend();
};

watch(
  () => messages.value.length,
  () => {
    scrollToBottom();
  },
);

watch(
  () => answerText.value,
  () => {
    if (isStreaming.value) {
      scrollToBottom();
    }
  },
);

watch(scrollToken, () => {
  scrollToBottom(true);
});

watch(
  () => route.params.conversationId,
  (conversationId) => {
    if (typeof conversationId === 'string' && conversationId !== currentConversationId.value) {
      currentConversationId.value = conversationId;
      fetchMessages();
    }
  },
);

watch(
  () => isStreaming.value,
  async (streaming) => {
    // 流式结束后：刷新消息列表，拿到后端真实 message_id（用于关键回答标记）
    if (!streaming && shouldRefreshAfterStream.value) {
      shouldRefreshAfterStream.value = false;
      try {
        await fetchMessages();
      } catch {
        // 刷新失败时不打断使用体验：保留当前 UI（local 消息仍在）
      }
    }
  },
);

onMounted(() => {
  fetchConversations();
  fetchDatasets();
  if (currentConversationId.value) {
    fetchMessages();
  }
});
</script>

<style scoped>
.chat-page {
  height: 100%;
}

.chat-sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
}

.sidebar-card {
  height: calc(100vh - 96px);
  overflow: hidden;
}

.sidebar-list {
  height: calc(100vh - 150px);
  overflow-y: auto;
  padding-right: 4px;
}

.message-list {
  max-height: 100%;
}

.markdown-body {
  color: inherit;
  line-height: 1.5;
  word-break: break-word;
}

.markdown-body a {
  color: #0ea5e9;
  text-decoration: underline;
}

.markdown-body p {
  margin: 0.25rem 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 1.25rem;
  margin: 0.25rem 0;
}

.markdown-body code {
  background: rgba(15, 23, 42, 0.05);
  border-radius: 4px;
  padding: 0.1rem 0.3rem;
  font-size: 0.95em;
}

</style>
