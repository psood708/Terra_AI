'use client';
import { useState, useEffect } from 'react';
import { useAppStore } from '@/store/appStore';
import { useDashboard } from '@/hooks/useDashboard';
import { Navbar } from '@/components/layout/Navbar';
import { PersonaSubheader } from '@/components/layout/PersonaSubheader';
import { OverviewTab } from '@/components/tabs/OverviewTab';
import { OdinAITab } from '@/components/tabs/OdinAITab';
import { GraphsTab } from '@/components/tabs/GraphsTab';
import { LongevityTab } from '@/components/tabs/LongevityTab';
import { HabitsTab } from '@/components/tabs/HabitsTab';
import { AiConfigModal } from '@/components/modals/AiConfigModal';
import { GuidedTour } from '@/components/tour/GuidedTour';

export default function DashboardPage() {
  const { selectedTab, setSelectedTab, currentPersona, hasSeenTour, setHasSeenTour } = useAppStore();
  const { persona, recovery, anomalies, workout, agp, hypnogram, correlation, bioAge, loading, refresh } = useDashboard(currentPersona);

  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [tourActive, setTourActive] = useState(false);

  // Auto-launch tour on first visit
  useEffect(() => {
    if (!hasSeenTour) {
      const t = setTimeout(() => setTourActive(true), 800);
      return () => clearTimeout(t);
    }
  }, []);

  const handleCloseTour = () => {
    setTourActive(false);
    setHasSeenTour(true);
    setSelectedTab('overview');
  };

  const handleStartTour = () => {
    setTourActive(true);
    setSelectedTab('overview');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar
        onOpenAiModal={() => setAiModalOpen(true)}
        onStartTour={handleStartTour}
        onRefresh={refresh}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        <PersonaSubheader
          persona={persona}
          anomalies={anomalies}
          onAskOdin={() => setSelectedTab('odin')}
        />

        {loading && selectedTab === 'overview' && (
          <div className="flex items-center justify-center h-40" style={{ color: 'var(--text-muted)' }}>
            <div className="text-sm animate-pulse">Loading live biometric telemetry...</div>
          </div>
        )}

        {/* Tab Panels */}
        {selectedTab === 'overview' && (
          <OverviewTab
            recovery={recovery}
            anomalies={anomalies}
            workout={workout}
            agp={agp}
            bioAge={bioAge}
            persona={persona}
            onAskOdin={() => setSelectedTab('odin')}
          />
        )}

        {selectedTab === 'odin' && (
          <OdinAITab
            anomalies={anomalies}
            onOpenAiModal={() => setAiModalOpen(true)}
          />
        )}

        {selectedTab === 'graphs' && (
          <GraphsTab
            agp={agp}
            hypnogram={hypnogram}
            correlation={correlation}
          />
        )}

        {selectedTab === 'longevity' && (
          <LongevityTab bioAge={bioAge} />
        )}

        {selectedTab === 'habits' && (
          <HabitsTab />
        )}
      </main>

      <AiConfigModal open={aiModalOpen} onClose={() => setAiModalOpen(false)} />

      <GuidedTour
        isActive={tourActive}
        onClose={handleCloseTour}
        onSwitchTab={(tab) => setSelectedTab(tab as any)}
      />
    </div>
  );
}
