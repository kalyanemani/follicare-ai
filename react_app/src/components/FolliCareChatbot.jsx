import React, { useState } from 'react';
import { useFolliCare } from '../context/FolliCareContext';

export function FolliCareChatbot({ isOpen, onClose }) {
  const { isDevMode, executeUICommand, setTelemetry } = useFolliCare();
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: 'Hello! I am your FolliCare AI Assistant. In Developer Mode, I use Qwen 2.5 Coder (7B) to update React components and live UI.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput('');
    setMessages(prev => [...prev, { sender: 'user', text: query }]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          mode: isDevMode ? 'developer' : 'customer',
          model_name: isDevMode ? 'qwen2.5-coder:7b' : 'qwen2.5:3b'
        })
      });

      const data = await res.json();
      const reply = data.reply_message || data.reply || 'Processed your request!';
      setMessages(prev => [...prev, { sender: 'agent', text: reply }]);

      if (data.trace || data.trace_id) {
        setTelemetry(data.trace || data);
      }

      if (data.ui_commands && Array.isArray(data.ui_commands)) {
        data.ui_commands.forEach(cmd => executeUICommand(cmd));
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { sender: 'agent', text: 'Error connecting to FolliCare backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', bottom: '90px', right: '24px', width: '380px',
      maxWidth: 'calc(100vw - 48px)', height: '520px', background: 'var(--bg-card)',
      backdropFilter: 'blur(20px)', border: '1px solid var(--border-focus)',
      borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', zIndex: 200,
      display: 'flex', flexDirection: 'column', overflow: 'hidden'
    }}>
      <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
          🌿 FolliCare AI ({isDevMode ? 'Qwen 2.5 Coder' : 'Qwen 2.5'})
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
      </div>

      <div style={{ flexGrow: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
              background: m.sender === 'user' ? 'var(--accent-color)' : 'var(--bg-secondary)',
              color: '#ffffff', padding: '10px 14px', borderRadius: 'var(--radius-md)',
              fontSize: '0.88rem', maxWidth: '85%', lineHeight: 1.45,
              border: m.sender === 'agent' ? '1px solid var(--border-color)' : 'none'
            }}
          >
            {m.text}
          </div>
        ))}
        {loading && <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Qwen 2.5 Coder is thinking & modifying UI...</div>}
      </div>

      <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={isDevMode ? "Ask UI developer (e.g. 'Add banner code SALE30')" : "Ask about hair care..."}
          style={{
            flexGrow: 1, background: 'var(--bg-primary)', border: '1px solid var(--border-color)',
            color: 'var(--text-primary)', padding: '8px 12px', borderRadius: 'var(--radius-md)', outline: 'none'
          }}
        />
        <button
          onClick={handleSend}
          style={{
            background: 'var(--accent-color)', color: '#ffffff', border: 'none',
            padding: '8px 16px', borderRadius: 'var(--radius-md)', fontWeight: 700, cursor: 'pointer'
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
