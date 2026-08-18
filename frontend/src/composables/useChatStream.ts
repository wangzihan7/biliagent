import { ref } from 'vue';
import type { ChatMetrics } from '@/types/api';
import { useAuthStore } from '@/stores/auth';

export interface ChatRequestPayload {
  user_id: string;
  conversation_id?: string;
  query: string;
  dataset_ids?: string[];
}

export function useChatStream() {
  const answerText = ref('');
  const metrics = ref<ChatMetrics | null>(null);
  const isStreaming = ref(false);
  const auth = useAuthStore();
  let controller: AbortController | null = null;

  function stopChat() {
    controller?.abort();
    controller = null;
    isStreaming.value = false;
  }

  async function startChat(
    payload: ChatRequestPayload,
    opts?: { onDone?: () => void },
  ) {
    // 停止之前的流，避免重复请求
    stopChat();
    isStreaming.value = true;
    answerText.value = '';
    metrics.value = null;
    // 创建可中断控制器，用于取消请求
    controller = new AbortController();

    // 发送 POST 请求到流式接口
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal: controller.signal, // 绑定中断信号
    });

    if (!res.ok || !res.body) {
      answerText.value = `⚠️ 请求失败（HTTP ${res.status}）`;
      isStreaming.value = false;
      opts?.onDone?.();
      return;
    }

    // 获取流式读取器
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = ''; // 缓冲区，用于累积不完整的数据块

    (async () => {
      try {
        while (true) {
          // 逐块读取流数据
          const { done, value } = await reader.read();
          if (done) break;

          // 解码二进制数据并统一换行符
          buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

          // 按 \n\n 分割 SSE 事件
          let sep: number;
          while ((sep = buf.indexOf('\n\n')) !== -1) {
            // 提取一个完整事件
            const raw = buf.slice(0, sep);
            // 从缓冲区移除已处理的事件
            buf = buf.slice(sep + 2);

            // 找到 data: 开头的行
            const line = raw.split('\n').find((l) => l.startsWith('data:'));
            if (!line) continue;

            try {
              // 解析 JSON 数据（去掉 "data:" 前缀）
              const data = JSON.parse(line.slice(5).trim());

              if (data.type === 'generation' && data.content) {
                // 生成中：追加文本内容
                answerText.value += data.content;
              } else if (data.type === 'done') {
                // 完成：保存指标，触发回调
                metrics.value = data.metrics;
                isStreaming.value = false;
                opts?.onDone?.();
              } else if (data.type === 'error') {
                // 错误：展示后端返回的错误信息并停止流
                answerText.value += (answerText.value ? '\n\n' : '') + `⚠️ ${data.content || '请求失败'}`;
                isStreaming.value = false;
                opts?.onDone?.();
              }
            } catch {}
          }
        }
      } catch {
        // 非用户主动中断时，重置状态
        if (!controller?.signal.aborted) isStreaming.value = false;
      }
    })();
  }

  return { answerText, metrics, isStreaming, startChat };
}
