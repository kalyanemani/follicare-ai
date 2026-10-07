import React, { useState } from 'react';
import { FolliCareProvider } from './context/FolliCareContext';
import { CopilotKitProvider, FolliCareCopilotPopup } from './components/CopilotKitIntegration';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { ProductCatalog } from './components/ProductCatalog';
import { DeveloperModePanel } from './components/DeveloperModePanel';
import './styles/theme.css';

export function FolliCareApp() {
  const [isDevPanelOpen, setIsDevPanelOpen] = useState(false);

  return (
    <div>
      <Navbar
        onOpenCart={() => alert('Shopping Bag Drawer')}
        onOpenRoutine={() => alert('Trichology Routine Builder')}
        onToggleDev={() => setIsDevPanelOpen(!isDevPanelOpen)}
      />
      <main>
        <Hero onConsult={() => {}} />
        <ProductCatalog />
      </main>

      <DeveloperModePanel
        isOpen={isDevPanelOpen}
        onClose={() => setIsDevPanelOpen(false)}
      />

      {/* CopilotKit Embedded AI Assistant */}
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
