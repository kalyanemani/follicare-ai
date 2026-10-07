import React from 'react';
import { useFolliCare } from '../context/FolliCareContext';

export function Navbar({ onOpenCart, onOpenRoutine, onToggleDev }) {
  const { theme, setTheme, cart, isDevMode, setIsDevMode } = useFolliCare();
  const cartCount = cart.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 100,
      backdropFilter: 'blur(16px)', background: 'rgba(10, 19, 15, 0.8)',
      borderBottom: '1px solid var(--border-color)', padding: '16px 32px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.4rem', fontWeight: 800 }}>
        <span style={{ fontSize: '1.8rem' }}>🌿</span>
        <span>FolliCare <small style={{ color: 'var(--accent-color)', fontSize: '0.65em' }}>React AI</small></span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          style={{
            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            border: '1px solid var(--border-color)', padding: '8px 14px',
            borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer'
          }}
        >
          <option value="botanical-emerald">🌿 Botanical Emerald</option>
          <option value="ruby-red">🔴 Velvet Ruby (Red)</option>
          <option value="ocean-blue">🌊 Clinical Sapphire (Blue)</option>
          <option value="rose-luxury">🌸 Rose Quartz (Pink)</option>
        </select>

        <button
          onClick={() => {
            setIsDevMode(!isDevMode);
            if (onToggleDev) onToggleDev();
          }}
          style={{
            background: isDevMode ? 'var(--accent-color)' : 'var(--bg-secondary)',
            color: isDevMode ? '#ffffff' : 'var(--text-primary)',
            border: '1px solid var(--border-color)', padding: '8px 14px',
            borderRadius: 'var(--radius-md)', fontWeight: 700, cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '6px'
          }}
        >
          🛠️ Dev Mode ({isDevMode ? 'ON' : 'OFF'})
        </button>

        <button
          onClick={onOpenRoutine}
          style={{
            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            border: '1px solid var(--border-color)', padding: '8px 14px',
            borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer'
          }}
        >
          📋 Routine Builder
        </button>

        <button
          onClick={onOpenCart}
          style={{
            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            border: '1px solid var(--border-color)', padding: '8px 14px',
            borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer'
          }}
        >
          🛍️ Bag ({cartCount})
        </button>
      </div>
    </header>
  );
}
