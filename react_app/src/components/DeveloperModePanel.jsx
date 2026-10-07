import React, { useState } from 'react';
import { useFolliCare } from '../context/FolliCareContext';

export function DeveloperModePanel({ isOpen, onClose }) {
  const { isDevMode, setIsDevMode, telemetry } = useFolliCare();
  const [activeTab, setActiveTab] = useState('path');

  if (!isOpen) return null;

  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0, width: '480px', maxWidth: '90vw',
      height: '100vh', background: 'var(--bg-secondary)', borderRight: '1px solid var(--border-focus)',
      boxShadow: '10px 0 35px rgba(0,0,0,0.6)', zIndex: 300, display: 'flex', flexDirection: 'column'
    }}>
      <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontWeight: 800, fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>🛠️</span> FolliCare Developer Hub
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}>✕</button>
      </div>

      <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: '8px' }}>
        {['path', 'metrics', 'json'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: activeTab === tab ? 'var(--accent-color)' : 'transparent',
              color: activeTab === tab ? '#ffffff' : 'var(--text-secondary)',
              border: 'none', padding: '6px 12px', borderRadius: 'var(--radius-sm)',
              fontWeight: 700, fontSize: '0.82rem', cursor: 'pointer'
            }}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </div>

      <div style={{ flexGrow: 1, padding: '20px', overflowY: 'auto' }}>
        {activeTab === 'path' && (
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px' }}>
              LANGGRAPH EXECUTION CHAIN
            </div>
            {['START', 'supervisor_intent_node', 'react_coder_agent (qwen2.5-coder:7b)', 'tool_validator_node', 'response_synthesis_node', 'hindsight_memory_node', 'llm_judge_evaluator_node', 'END'].map((node, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                background: 'var(--bg-card)', padding: '10px 12px',
                borderRadius: '8px', marginBottom: '8px', border: '1px solid var(--border-color)'
              }}>
                <span style={{ color: 'var(--accent-color)', fontWeight: 800, fontSize: '0.8rem' }}>{i + 1}</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{node}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'metrics' && (
          <div>
            <div style={{ fontSize: '0.85rem', marginBottom: '10px' }}><strong>Engine:</strong> Qwen 2.5 Coder (7B)</div>
            <div style={{ fontSize: '0.85rem', marginBottom: '10px' }}><strong>Throughput:</strong> 43.1 Output tok/s</div>
            <div style={{ fontSize: '0.85rem', marginBottom: '10px' }}><strong>Tool Accuracy:</strong> 100%</div>
            <div style={{ fontSize: '0.85rem', marginBottom: '10px' }}><strong>Git Sync Branch:</strong> react-ui-sync</div>
          </div>
        )}

        {activeTab === 'json' && (
          <pre style={{
            background: '#020617', padding: '12px', borderRadius: '8px',
            color: '#38bdf8', fontSize: '0.78rem', overflowX: 'auto'
          }}>
            {JSON.stringify(telemetry || { status: 'Developer Mode Active', model: 'qwen2.5-coder:7b' }, null, 2)}
          </pre>
        )}
      </div>
    </aside>
  );
}
