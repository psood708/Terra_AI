import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { PersonaId, Provider, TabId } from '@/types/api';

interface AppState {
  // Navigation
  selectedTab: TabId;
  setSelectedTab: (tab: TabId) => void;

  // Persona
  currentPersona: PersonaId;
  setCurrentPersona: (id: PersonaId) => void;

  // AI Config
  activeApiKey: string;
  activeProvider: Provider;
  setAiConfig: (key: string, provider: Provider) => void;
  clearAiConfig: () => void;

  // Tour
  hasSeenTour: boolean;
  setHasSeenTour: (v: boolean) => void;

  // Streak
  currentStreak: number;
  setStreak: (n: number) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedTab: 'overview',
      setSelectedTab: (tab) => set({ selectedTab: tab }),

      currentPersona: 'alex_longevity',
      setCurrentPersona: (id) => set({ currentPersona: id }),

      activeApiKey: '',
      activeProvider: 'huggingface',
      setAiConfig: (key, provider) => set({ activeApiKey: key, activeProvider: provider }),
      clearAiConfig: () => set({ activeApiKey: '', activeProvider: 'huggingface' }),

      hasSeenTour: false,
      setHasSeenTour: (v) => set({ hasSeenTour: v }),

      currentStreak: 12,
      setStreak: (n) => set({ currentStreak: n }),
    }),
    {
      name: 'terra-app-store',
      partialize: (s) => ({
        currentPersona: s.currentPersona,
        activeApiKey: s.activeApiKey,
        activeProvider: s.activeProvider,
        hasSeenTour: s.hasSeenTour,
        currentStreak: s.currentStreak,
      }),
    }
  )
);
