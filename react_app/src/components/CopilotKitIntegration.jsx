import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useFolliCare } from '../context/FolliCareContext';
import { MessageSquare, Sparkles, X, Send, Bot, Code, Cpu, Layers } from 'lucide-react';

// Copilot Registry for readable contexts and executable actions
const CopilotContext = createContext({
  readables: {},
  actions: {},
  registerReadable: () => {},
  unregisterReadable: () => {},
  registerAction: () => {},
  unregisterAction: () => {},
  executeAction: async () => {}
});

export function CopilotKitProvider({ children, runtimeUrl = '/api/chat' }) {
  const [readables, setReadables] = useState({});
  const [actions, setActions] = useState({});

  const registerReadable = (id, description, value) => {
    setReadables(prev => ({ ...prev, [id]: { description, value } }));
  };

  const unregisterReadable = (id) => {
    setReadables(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const registerAction = (name, actionDef) => {
    setActions(prev => ({ ...prev, [name]: actionDef }));
  };

  const unregisterAction = (name) => {
    setActions(prev => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
  };

  const executeAction = async (actionName, params) => {
    const act = actions[actionName];
    if (act && act.handler) {
      return await act.handler(params);
    }
    console.warn(`[CopilotKit] Action '${actionName}' not registered.`);
    return null;
  };

  return (
    <CopilotContext.Provider value={{
      readables,
      actions,
      registerReadable,
      unregisterReadable,
      registerAction,
      unregisterAction,
      executeAction,
      runtimeUrl
    }}>
      {children}
    </CopilotContext.Provider>
  );
}

/**
 * useCopilotReadable - Exposes component state & DOM elements to AI
 */
export function useCopilotReadable({ description, value, parentId = '' }) {
  const { registerReadable, unregisterReadable } = useContext(CopilotContext);
  const idRef = useRef(parentId || `readable_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    registerReadable(idRef.current, description, value);
    return () => unregisterReadable(idRef.current);
  }, [description, value]);
}

/**
 * useCopilotAction - Registers an executable action for AI LLM/agents
 */
export function useCopilotAction({ name, description, parameters = [], handler }) {
  const { registerAction, unregisterAction } = useContext(CopilotContext);

  useEffect(() => {
    registerAction(name, { description, parameters, handler });
    return () => unregisterAction(name);
  }, [name, description, JSON.stringify(parameters), handler]);
}

/**
 * CopilotSidebar / CopilotPopup UI Component
 */
export function FolliCareCopilotPopup() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: '👋 Hi! I am your FolliCare Copilot powered by LangGraph & CopilotKit. Ask me by voice or text to reduce card sizes, update prices, switch themes, or upload scalp photos!',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'actions' | 'state'
  const { readables, actions, executeAction, runtimeUrl } = useContext(CopilotContext);
  const { isDevMode, executeUICommand } = useFolliCare();
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  // Initialize Web Speech API Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = 'en-US';

      recog.onstart = () => setIsListening(true);
      recog.onend = () => setIsListening(false);
      recog.onerror = (e) => {
        console.error('Speech recognition error:', e);
        setIsListening(false);
      };
      recog.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInput(transcript);
          sendMessage(transcript);
        }
      };
      recognitionRef.current = recog;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please use Chrome/Edge.');
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  const speakText = (text) => {
    if (!isVoiceEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*_`#]/g, '').replace(/[\u{1F600}-\u{1F64F}]/gu, '');
    const utter = new SpeechSynthesisUtterance(cleanText);
    utter.rate = 1.05;
    utter.pitch = 1.0;
    window.speechSynthesis.speak(utter);
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async () => {
      const base64 = reader.result;
      const userMsg = {
        role: 'user',
        text: `📸 Uploaded Scalp / Hair Image (${file.name}) for Multimodal Vision diagnosis`,
        image: base64,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const resp = await fetch('/api/multimodal/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: base64,
            prompt: 'Analyze this scalp/hair image. Identify the hair condition, texture, and recommend botanical treatments.'
          })
        });
        const data = await resp.json();
        const analysis = data.vision_analysis?.analysis || 'Visual diagnosis complete.';
        const botReply = {
          role: 'assistant',
          text: `🔬 **Vision RAG Analysis (Qwen 2.5-VL)**:\n${analysis}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, botReply]);
        speakText(analysis);
      } catch (err) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: `⚠️ Vision diagnosis failed: ${err.message}`,
          isError: true,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      } finally {
        setIsLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const sendMessage = async (userText) => {
    if (!userText.trim() || isLoading) return;

    setInput('');
    const userMsg = {
      role: 'user',
      text: userText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await fetch(runtimeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          mode: isDevMode ? 'developer' : 'customer',
          copilot_context: {
            readables: Object.values(readables).map(r => ({ description: r.description, value: r.value })),
            registered_actions: Object.keys(actions)
          }
        })
      });

      const data = await response.json();
      
      // Execute registered CopilotKit actions and trigger live React Context mutations
      if (data.ui_commands && Array.isArray(data.ui_commands)) {
        for (const cmd of data.ui_commands) {
          if (executeUICommand) executeUICommand(cmd);
          const actName = cmd.action || cmd.command;
          if (actions[actName]) {
            await executeAction(actName, cmd.payload || cmd);
          }
        }
      }

      const replyText = data.reply || data.reply_message || 'Action executed successfully.';
      const botReply = {
        role: 'assistant',
        text: replyText,
        intent: data.intent,
        ui_commands: data.ui_commands,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botReply]);
      speakText(replyText);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: `⚠️ Copilot communication error: ${err.message}`,
          isError: true,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = (e) => {
    e?.preventDefault();
    sendMessage(input);
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            background: 'linear-gradient(135deg, var(--accent-color, #10b981) 0%, #059669 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '9999px',
            padding: '14px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: '0 10px 25px rgba(16, 185, 129, 0.35)',
            cursor: 'pointer',
            fontWeight: 700,
            fontSize: '0.95rem',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
          className="copilot-fab"
        >
          <Sparkles size={18} />
          <span>FolliCare Copilot</span>
        </button>
      )}

      {/* Copilot Popup Window */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '420px',
          maxWidth: 'calc(100vw - 48px)',
          height: '600px',
          maxHeight: 'calc(100vh - 48px)',
          background: 'rgba(17, 24, 20, 0.96)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '20px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(16, 185, 129, 0.15)',
          zIndex: 10000,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'copilotSlideUp 0.3s ease-out'
        }}>
          {/* Header */}
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            background: 'rgba(255, 255, 255, 0.03)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                background: 'var(--accent-color, #10b981)',
                padding: '6px',
                borderRadius: '8px',
                display: 'flex',
                color: '#fff'
              }}>
                <Sparkles size={16} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>FolliCare Copilot</h4>
                <span style={{ fontSize: '0.72rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
                  CopilotKit Connected (React 18 State)
                </span>
              </div>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation Tabs (Chat | Registered Actions | Live State) */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            background: 'rgba(0, 0, 0, 0.2)'
          }}>
            {[
              { id: 'chat', label: 'Copilot Chat', icon: MessageSquare },
              { id: 'actions', label: `Actions (${Object.keys(actions).length})`, icon: Code },
              { id: 'state', label: `UI Context (${Object.keys(readables).length})`, icon: Layers }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    flex: 1,
                    padding: '8px 10px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    background: isActive ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                    color: isActive ? '#10b981' : '#9ca3af',
                    border: 'none',
                    borderBottom: isActive ? '2px solid #10b981' : '2px solid transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <Icon size={13} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Body Content */}
          {activeTab === 'chat' && (
            <div style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '85%',
                    background: m.role === 'user'
                      ? 'linear-gradient(135deg, var(--accent-color, #10b981) 0%, #059669 100%)'
                      : 'rgba(255, 255, 255, 0.06)',
                    color: '#ffffff',
                    padding: '10px 14px',
                    borderRadius: m.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                    border: m.role === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
                    fontSize: '0.86rem',
                    lineHeight: '1.45',
                    position: 'relative'
                  }}
                >
                  <div>{m.text}</div>
                  {m.ui_commands && m.ui_commands.length > 0 && (
                    <div style={{
                      marginTop: '6px',
                      padding: '4px 8px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                      fontFamily: 'monospace',
                      color: '#34d399'
                    }}>
                      ⚡ Triggered Action: {m.ui_commands.map(c => c.action || c.command).join(', ')}
                    </div>
                  )}
                  <span style={{
                    fontSize: '0.65rem',
                    color: 'rgba(255, 255, 255, 0.4)',
                    display: 'block',
                    textAlign: 'right',
                    marginTop: '4px'
                  }}>
                    {m.time}
                  </span>
                </div>
              ))}
              {isLoading && (
                <div style={{
                  alignSelf: 'flex-start',
                  background: 'rgba(255, 255, 255, 0.06)',
                  padding: '10px 14px',
                  borderRadius: '14px 14px 14px 2px',
                  fontSize: '0.8rem',
                  color: '#9ca3af',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Sparkles size={14} className="spin" />
                  <span>Copilot reasoning with LangGraph & Ollama...</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}

          {activeTab === 'actions' && (
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
              <p style={{ fontSize: '0.78rem', color: '#9ca3af', margin: '0 0 12px' }}>
                Functions callable directly by the AI model via <code style={{ color: '#10b981' }}>useCopilotAction()</code>:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.entries(actions).map(([name, act]) => (
                  <div key={name} style={{
                    padding: '10px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px'
                  }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', fontFamily: 'monospace' }}>
                      {name}()
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#d1d5db', marginTop: '3px' }}>
                      {act.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'state' && (
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
              <p style={{ fontSize: '0.78rem', color: '#9ca3af', margin: '0 0 12px' }}>
                Live component state exposed to the AI model via <code style={{ color: '#10b981' }}>useCopilotReadable()</code>:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.entries(readables).map(([id, r]) => (
                  <div key={id} style={{
                    padding: '10px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px'
                  }}>
                    <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#60a5fa' }}>
                      {r.description}
                    </div>
                    <pre style={{
                      fontSize: '0.68rem',
                      color: '#9ca3af',
                      marginTop: '6px',
                      background: 'rgba(0,0,0,0.4)',
                      padding: '6px',
                      borderRadius: '4px',
                      overflowX: 'auto'
                    }}>
                      {JSON.stringify(r.value, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Input with Voice & Vision */}
          <form
            onSubmit={handleSend}
            style={{
              padding: '12px 16px',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              background: 'rgba(0, 0, 0, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {/* Hidden File Input for Scalp Vision */}
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleImageUpload}
            />

            {/* Scalp Vision Upload Button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Upload Scalp / Hair Photo for Multimodal Vision Analysis"
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#60a5fa',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '10px',
                padding: '9px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease'
              }}
            >
              📷
            </button>

            {/* Voice Input (Speech-to-Text) Button */}
            <button
              type="button"
              onClick={toggleListening}
              title={isListening ? 'Listening... Click to Stop' : 'Click for Voice Input'}
              style={{
                background: isListening ? '#ef4444' : 'rgba(255, 255, 255, 0.08)',
                color: '#ffffff',
                border: isListening ? '1px solid #f87171' : '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '10px',
                padding: '9px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                animation: isListening ? 'pulse 1s infinite' : 'none',
                transition: 'all 0.2s ease'
              }}
            >
              {isListening ? '🎙️🔴' : '🎙️'}
            </button>

            {/* Voice Output (TTS) Toggle */}
            <button
              type="button"
              onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
              title={isVoiceEnabled ? 'Voice Output ON' : 'Voice Output Muted'}
              style={{
                background: 'transparent',
                color: isVoiceEnabled ? 'var(--accent-color, #10b981)' : '#6b7280',
                border: 'none',
                padding: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {isVoiceEnabled ? '🔊' : '🔇'}
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isListening ? 'Listening to voice...' : "Voice or type (e.g. 'Reduce card size of rosemary oil')"}
              style={{
                flex: 1,
                padding: '10px 14px',
                background: 'rgba(255, 255, 255, 0.06)',
                border: isListening ? '1px solid var(--accent-color, #10b981)' : '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '10px',
                color: '#ffffff',
                fontSize: '0.84rem',
                outline: 'none',
                transition: 'border 0.2s'
              }}
            />

            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              style={{
                background: 'var(--accent-color, #10b981)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                padding: '10px 14px',
                cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
                opacity: isLoading || !input.trim() ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
