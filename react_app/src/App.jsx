import React, { useState } from 'react';
import { FolliCareProvider } from './context/FolliCareContext';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { ProductCatalog } from './components/ProductCatalog';
import { DeveloperModePanel } from './components/DeveloperModePanel';
import { FolliCareChatbot } from './components/FolliCareChatbot';
import './styles/theme.css';

export function FolliCareApp() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isDevPanelOpen, setIsDevPanelOpen] = useState(false);

  return (
    <div>
      <Navbar
        onOpenCart={() => alert('Shopping Bag Drawer')}
        onOpenRoutine={() => alert('Trichology Routine Builder')}
        onToggleDev={() => setIsDevPanelOpen(!isDevPanelOpen)}
      />
      <main>
        <Hero onConsult={() => setIsChatOpen(true)} />
        <ProductCatalog />
      </main>

      <DeveloperModePanel
        isOpen={isDevPanelOpen}
        onClose={() => setIsDevPanelOpen(false)}
      />

      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 200 }}>
        <button
          onClick={() => setIsChatOpen(!isChatOpen)}
          style={{
            background: 'var(--accent-color)', color: '#ffffff', width: '60px', height: '60px',
            borderRadius: '9999px', border: 'none', fontSize: '1.8rem', cursor: 'pointer',
            boxShadow: '0 8px 24px var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}
        >
          🌿
        </button>
      </div>

      <FolliCareChatbot
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <FolliCareProvider>
      <FolliCareApp />
    </FolliCareProvider>
  );
}
