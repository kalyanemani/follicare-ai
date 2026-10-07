import React, { useState, useEffect } from 'react';
import { useFolliCare } from '../context/FolliCareContext';
import { X, Sparkles, CheckCircle2, ShoppingBag } from 'lucide-react';

export function RoutineModal({ isOpen, onClose }) {
  const [selectedConcern, setSelectedConcern] = useState('Hair Fall & Thinning');
  const [routineData, setRoutineData] = useState(null);
  const [loading, setLoading] = useState(false);
  const { addToCart } = useFolliCare();

  const concerns = [
    'Hair Fall & Thinning',
    'Dandruff & Oily Scalp',
    'Damaged & Dry Hair',
    'Curly, Coily & Wavy (3A-4C)',
    'Frizz & Heat Protection'
  ];

  useEffect(() => {
    if (isOpen) {
      fetchRoutine(selectedConcern);
    }
  }, [isOpen, selectedConcern]);

  const fetchRoutine = async (concern) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/routine?concern=${encodeURIComponent(concern)}`);
      const data = await res.json();
      if (data.routine) setRoutineData(data.routine);
    } catch (e) {
      console.error('Failed to fetch routine:', e);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{
        background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
        borderRadius: '24px', width: '750px', maxWidth: '100%', maxHeight: '90vh',
        overflowY: 'auto', padding: '32px', boxShadow: '0 25px 60px rgba(0,0,0,0.6)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-color)', fontWeight: 700, textTransform: 'uppercase' }}>
              Trichological Regimen Architect
            </span>
            <h2 style={{ margin: '4px 0 0', fontSize: '1.5rem', fontWeight: 800 }}>
              Personalized Hair Protocol
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        {/* Concern Selector */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '24px' }}>
          {concerns.map(c => (
            <button
              key={c}
              onClick={() => setSelectedConcern(c)}
              style={{
                padding: '8px 14px', borderRadius: '9999px', fontSize: '0.82rem', fontWeight: 600,
                background: selectedConcern === c ? 'var(--accent-color)' : 'var(--bg-card)',
                color: selectedConcern === c ? '#ffffff' : 'var(--text-secondary)',
                border: '1px solid var(--border-color)', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              {c}
            </button>
          ))}
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            <Sparkles size={28} className="spin" style={{ margin: '0 auto 12px', display: 'block', color: 'var(--accent-color)' }} />
            <span>Consulting trichology knowledge base & synthesizing steps...</span>
          </div>
        ) : routineData ? (
          <div>
            <div style={{
              background: 'var(--bg-card)', padding: '16px 20px', borderRadius: '16px',
              border: '1px solid var(--border-color)', marginBottom: '24px'
            }}>
              <h4 style={{ margin: '0 0 6px', color: 'var(--accent-color)', fontSize: '1rem' }}>
                {routineData.routineName}
              </h4>
              <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                {routineData.scientificRationale}
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
              {(routineData.steps || []).map((step, idx) => (
                <div key={idx} style={{
                  display: 'flex', gap: '14px', alignItems: 'flex-start',
                  background: 'rgba(255,255,255,0.03)', padding: '14px 18px',
                  borderRadius: '12px', border: '1px solid var(--border-color)'
                }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    background: 'var(--accent-color)', color: '#ffffff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 800, fontSize: '0.85rem', flexShrink: 0
                  }}>
                    {idx + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h5 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>{step.stepName}</h5>
                      <span style={{ fontSize: '0.75rem', color: 'var(--accent-color)', fontWeight: 600 }}>{step.frequency}</span>
                    </div>
                    <p style={{ margin: '4px 0 6px', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                      Product: <strong>{step.product}</strong>
                    </p>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {step.technique}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => {
                  (routineData.steps || []).forEach(s => {
                    addToCart({
                      id: `prod_routine_${Math.random().toString(36).substr(2, 6)}`,
                      name: s.product,
                      price: 28.99,
                      icon: '🌿'
                    }, 1);
                  });
                  alert('Added complete routine kit to your shopping bag!');
                  onClose();
                }}
                style={{
                  flex: 1, padding: '12px', background: 'var(--accent-color)', color: '#ffffff',
                  border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 700,
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                }}
              >
                <ShoppingBag size={18} />
                <span>Add Complete Routine Kit to Bag</span>
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
