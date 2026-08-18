//对话api
import http from './http';
import type { Conversation, Message } from '@/types/api';

export function createConversation(payload: {
  user_id: string;
  conversation_name: string;
  topic_id?: string;
}) {
  return http.post<Conversation>('/conversations', payload);
}

export function getConversation(conversationId: string) {
  return http.get<Conversation>(`/conversations/${conversationId}`);
}

export function listUserConversations(userId: string, params?: { limit?: number }) {
  return http.get<Conversation[]>(`/users/${userId}/conversations`, { params });
}

export function updateConversation(conversationId: string, payload: { conversation_name: string }) {
  return http.put<Conversation>(`/conversations/${conversationId}`, payload);
}

export function deleteConversation(conversationId: string) {
  return http.delete<void>(`/conversations/${conversationId}`);
}

export function getMessages(conversationId: string, params?: { limit?: number }) {
  return http.get<Message[]>(`/conversations/${conversationId}/messages`, { params });
}

export function markMessageImportant(messageId: string, isImportant: boolean) {
  return http.post(`/messages/${messageId}/important`, { is_important: isImportant });
}
