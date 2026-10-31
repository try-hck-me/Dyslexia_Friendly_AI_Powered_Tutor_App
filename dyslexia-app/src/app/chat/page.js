'use client';
import AppShell from '@/components/layout/AppShell';
import TTSButton from '@/components/tts/TTSButton';
import { useUser } from '@/context/UserContext';
import { useState, useRef, useEffect } from 'react';
import { sendChat, getChatHistory } from '@/lib/api';
import { Send, Loader2, BookOpen, Mic, MicOff, History } from 'lucide-react';

export default function ChatPage() {
  const { effectiveUserId } = useUser();
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [loadingHist, setLoadingHist] = useState(true);
  const [listening, setListening] = useState(false);
  const endRef          = useRef(null);
  const recognitionRef  = useRef(null);

  // Smooth-scroll to bottom whenever messages change
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Load chat history from backend on mount
  useEffect(() => {
    if (!effectiveUserId) return;
    setLoadingHist(true);
    getChatHistory(effectiveUserId, 30)
      .then(res => {
        if (res.success && res.data?.history?.length > 0) {
          // Map DB history rows to message bubble format
          const hist = res.data.history.flatMap(row => [
            { role: 'user', text: row.question },
            { role: 'bot',  text: row.answer,  sources: [] },
          ]);
          setMessages(hist);
        }
      })
      .catch(() => { /* history unavailable — start fresh */ })
      .finally(() => setLoadingHist(false));
  }, [effectiveUserId]);

  // Send a question to the RAG chatbot
  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setLoading(true);
    try {
      const res = await sendChat(effectiveUserId, q);
      if (res.success) {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: res.data.answer,
          sources: res.data.sources || [],
          contextFound: res.data.context_found,
          detailMode: res.data.detail_mode,
          source: res.data.source,   // "notes" | "general_knowledge"
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: res.error || 'Something went wrong. Please try again.',
          isError: true,
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: err.message || 'Failed to connect to the server.',
        isError: true,
      }]);
    }
    setLoading(false);
  };

  // Voice input
  const toggleVoice = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Voice input is not supported in this browser. Try Chrome.');
      return;
    }
    if (listening) { recognitionRef.current?.stop(); setListening(false); return; }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-US';
    rec.onresult = e => setInput(prev => (prev + ' ' + e.results[0][0].transcript).trim());
    rec.onend    = () => setListening(false);
    rec.onerror  = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
    setListening(true);
  };

  return (
    <AppShell fullWidth>
      <div className="page-header flex-between" style={{ marginBottom: 'var(--space-md)' }}>
        <div>
          <h1 className="page-title">Study Bot</h1>
          <p className="page-subtitle">Ask anything — about your notes or any topic. I&apos;ll answer in simple, clear language.</p>
        </div>
        {messages.length > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={() => setMessages([])} title="Clear session">
            Clear chat
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="card" style={{ padding: 0, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-lg)' }}>

          {/* Loading history indicator */}
          {loadingHist && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', marginBottom: 'var(--space-md)' }}>
              <History size={14}/> Loading previous messages…
            </div>
          )}

          {/* Empty state */}
          {!loadingHist && messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon"><BookOpen size={48} color="var(--accent)" style={{ opacity: 0.4 }}/></div>
              <p className="empty-text">Ask me anything! Upload a PDF to get answers from your notes, or just ask any question.</p>
            </div>
          )}

          <div className="chat-list">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-row ${msg.role === 'user' ? 'chat-row-user' : 'chat-row-bot'}`}>
                <div style={{ maxWidth: '85%', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  {/* Detail-mode badge */}
                  {msg.detailMode && (
                    <div style={{ marginBottom: 4 }}>
                      <span className="badge" style={{ fontSize: 'var(--fs-xs)', background: 'rgba(124,92,252,0.1)', color: 'var(--accent)' }}>
                        📝 Detailed answer
                      </span>
                    </div>
                  )}

                  {/* General knowledge badge */}
                  {msg.source === 'general_knowledge' && (
                    <div style={{ marginBottom: 4 }}>
                      <span className="badge" style={{ fontSize: 'var(--fs-xs)', background: 'rgba(234,179,8,0.12)', color: '#ca8a04', border: '1px solid rgba(234,179,8,0.3)' }}>
                        🌐 General knowledge
                      </span>
                    </div>
                  )}

                  <div
                    className={`chat-bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-bot'}`}
                    style={msg.isError ? { background: 'var(--error)' } : {}}
                  >
                    <div
                      dangerouslySetInnerHTML={{
                        __html: msg.text
                          .replace(/\n/g, '<br/>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/• /g, '&bull; '),
                      }}
                    />
                  </div>

                  {msg.role === 'bot' && !msg.isError && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', marginTop: 'var(--space-xs)' }}>
                      <TTSButton text={msg.text} size={14}/>
                      {msg.sources?.length > 0 && (
                        <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                          From: {msg.sources.map(s => s.source).filter(Boolean).slice(0, 3).join(', ')}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="chat-row chat-row-bot">
                <div className="chat-bubble bubble-bot" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Loader2 size={16} style={{ animation: 'spin .8s linear infinite' }}/> Thinking…
                </div>
              </div>
            )}
            <div ref={endRef}/>
          </div>
        </div>

        {/* Input row */}
        <div style={{ borderTop: '1px solid var(--border)', padding: 'var(--space-md)', display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
          <button className="btn-icon" onClick={toggleVoice}
            title={listening ? 'Stop listening' : 'Voice input (Chrome)'}
            style={{ color: listening ? 'var(--error)' : 'var(--text-muted)', flexShrink: 0 }}>
            {listening ? <MicOff size={20}/> : <Mic size={20}/>}
          </button>
          <input
            type="text"
            className="input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask anything — your notes or any topic…"
            disabled={loading}
            maxLength={1000}
            style={{ flex: 1, minHeight: 44 }}
          />
          <button className="btn btn-primary" onClick={send}
            disabled={loading || !input.trim()}
            aria-label="Send message" style={{ flexShrink: 0 }}>
            <Send size={18}/>
          </button>
        </div>
      </div>
    </AppShell>
  );
}
