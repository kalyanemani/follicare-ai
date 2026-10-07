import React from 'react';
import { useFolliCare } from '../context/FolliCareContext';

export function Hero({ onConsult }) {
  const { heroContent, activeBanner } = useFolliCare();

  return (
    <div>
      {/* Announcement Banner */}
      <div style={{
        background: 'var(--banner-bg)', color: '#ffffff',
        padding: '10px 20px', textAlign: 'center', fontWeight: 600,
        fontSize: '0.92rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px'
      }}>
        <span>{activeBanner.message}</span>
        {activeBanner.code && (
          <span style={{ background: 'rgba(255,255,255,0.25)', padding: '2px 10px', borderRadius: '9999px', fontFamily: 'monospace' }}>
            USE CODE: {activeBanner.code}
          </span>
        )}
      </div>

      {/* Hero Section */}
      <section style={{
        background: 'var(--hero-bg)', padding: '60px 32px 40px',
        textAlign: 'center', maxWidth: '1200px', margin: '0 auto'
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: 'var(--bg-accent)', border: '1px solid var(--border-color)',
          color: 'var(--accent-color)', padding: '6px 16px', borderRadius: '9999px',
          fontSize: '0.85rem', fontWeight: 700, marginBottom: '20px'
        }}>
          ✨ Powered by Local Ollama & Multi-Agent LangGraph
        </div>
        <h1 style={{ fontSize: '3rem', fontWeight: 900, lineHeight: 1.15, marginBottom: '16px' }}>
          {heroContent.title}
        </h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', maxWidth: '700px', margin: '0 auto 30px' }}>
          {heroContent.subtitle}
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
          <button
            onClick={onConsult}
            style={{
              background: 'var(--accent-color)', color: '#ffffff', border: 'none',
              padding: '12px 24px', borderRadius: 'var(--radius-md)', fontWeight: 700,
              cursor: 'pointer', boxShadow: '0 4px 14px var(--accent-glow)'
            }}
          >
            💬 Consult AI Trichologist
          </button>
        </div>
      </section>
    </div>
  );
}

// [Qwen 2.5 Coder Auto-Update]: Updated Hero announcement banner with coupon code 'FLASH50'. (2026-10-07 08:33:03)

// [Qwen 2.5 Coder Auto-Update]: Updated Hero announcement banner with coupon code 'BOTANICAL30'. (2026-10-07 08:34:22)
