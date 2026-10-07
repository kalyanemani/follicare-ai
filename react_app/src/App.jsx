import React, { useState } from 'react';
import { FolliCareProvider } from './context/FolliCareContext';
import { CopilotKitProvider, FolliCareCopilotPopup } from './components/CopilotKitIntegration';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { ProductCatalog } from './components/ProductCatalog';
import { DeveloperModePanel } from './components/DeveloperModePanel';
import { CartDrawer } from './components/CartDrawer';
import { RoutineModal } from './components/RoutineModal';
import './styles/theme.css';

export function FolliCareApp() {
  const [isDevPanelOpen, setIsDevPanelOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isRoutineOpen, setIsRoutineOpen] = useState(false);

  return (
    <div>
      <Navbar
        onOpenCart={() => setIsCartOpen(true)}
        onOpenRoutine={() => setIsRoutineOpen(true)}
        onToggleDev={() => setIsDevPanelOpen(!isDevPanelOpen)}
      />
      <main>
        <Hero
          onConsult={() => {}}
          onOpenRoutine={() => setIsRoutineOpen(true)}
        />
        <ProductCatalog />
      </main>

      {/* Interactive Modals & Drawers */}
      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
      />

      <RoutineModal
        isOpen={isRoutineOpen}
        onClose={() => setIsRoutineOpen(false)}
      />

      <DeveloperModePanel
        isOpen={isDevPanelOpen}
        onClose={() => setIsDevPanelOpen(false)}
      />

      {/* CopilotKit Embedded AI Assistant with Voice STT/TTS & Vision */}
      <FolliCareCopilotPopup />
    </div>
  );
}

export default function App() {
  return (
    <FolliCareProvider>
      <CopilotKitProvider runtimeUrl="/api/chat">
        <FolliCareApp />
      </CopilotKitProvider>
    </FolliCareProvider>
  );
}
