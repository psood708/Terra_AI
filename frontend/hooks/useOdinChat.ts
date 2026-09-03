'use client';
import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { ChatMessage, PersonaId, Provider } from '@/types/api';

export function useOdinChat(personaId: PersonaId, apiKey: string, provider: Provider) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'odin',
      content: 'Hello! I am **OdinAI**, your health intelligence companion on Terra\'s unified data infrastructure. Ask me anything about your recovery score, sleep architecture, glycemic variability, or training adaptation. Every insight is grounded in peer-reviewed clinical research.',
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await api.askOdin({
        persona_id: personaId,
        query,
        api_key: apiKey || undefined,
        provider,
      });

      const odinMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'odin',
        content: res.odin_response,
        isLiveAi: res.is_live_ai,
        modelName: res.model_name,
        provider: res.provider,
        llmError: res.llm_error,
        citations: res.scientific_citations,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, odinMsg]);
    } catch (err) {
      console.error('OdinAI query failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [personaId, apiKey, provider, isLoading]);

  return { messages, isLoading, sendMessage };
}
