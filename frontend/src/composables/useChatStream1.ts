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
    stopChat();
    isStreaming.value = true;
    answerText.value = '';
    metrics.value = null;
    controller = new AbortController();

    const res = await fetch(`${import.meta.env.VITE_API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok || !res.body) {
      isStreaming.value = false;
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

          let sep: number;
          while ((sep = buf.indexOf('\n\n')) !== -1) {
            const raw = buf.slice(0, sep);
            buf = buf.slice(sep + 2);
            const line = raw.split('\n').find((l) => l.startsWith('data:'));
            if (!line) continue;
            try {
              const data = JSON.parse(line.slice(5).trim());
              if (data.type === 'generation' && data.content) {
                answerText.value += data.content;
              } else if (data.type === 'done') {
                metrics.value = data.metrics;
                isStreaming.value = false;
                opts?.onDone?.();
              } else if (data.type === 'error') {
                isStreaming.value = false;
              }
            } catch {}
          }
        }
      } catch {
        if (!controller?.signal.aborted) isStreaming.value = false;
      }
    })();
  }

  return { answerText, metrics, isStreaming, startChat };
}
