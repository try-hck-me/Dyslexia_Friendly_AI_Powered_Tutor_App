'use client';
import AppShell from '@/components/layout/AppShell';
import TTSButton from '@/components/tts/TTSButton';
import { useUser } from '@/context/UserContext';
import { useState, useRef, useEffect } from 'react';
import { sendFriendly } from '@/lib/api';
import { Send, Loader2, Heart } from 'lucide-react';
import { MOOD_COLORS } from '@/lib/constants';

export default function FriendlyPage() {
  const { effectiveUserId } = useUser();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const res = await sendFriendly(effectiveUserId, msg);
      if (res.success) {
        setMessages(prev => [...prev, { role: 'bot', text: res.data.response, mood: res.data.mood }]);
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: 'I had a small problem. Can you try again?', isError: true }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: err.message, isError: true }]);
    }
    setLoading(false);
  };

  const getMoodStyle = (mood) => {
    const m = mood?.toLowerCase() || 'neutral';
    for (const key of Object.keys(MOOD_COLORS)) {
      if (m.includes(key)) return MOOD_COLORS[key];
    }
    return MOOD_COLORS.neutral;
  };

  return (
    <AppShell fullWidth>
      <div className="page-header" style={{ marginBottom: 'var(--space-md)' }}>
        <h1 className="page-title">FriendlyBot</h1>
        <p className="page-subtitle">I&apos;m here to listen and support you. Tell me how you&apos;re feeling.</p>
      </div>

      <div className="card" style={{ padding: 0, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-lg)' }}>
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon"><Heart size={48} color="var(--accent2)" style={{ opacity: 0.4 }}/></div>
              <p className="empty-text">Hi there! I&apos;m your support buddy. Tell me how you&apos;re feeling or what&apos;s on your mind.</p>
            </div>
          )}

          <div className="chat-list">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-row ${msg.role === 'user' ? 'chat-row-user' : 'chat-row-bot'}`}>
                <div style={{ maxWidth: '85%', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.mood && (
                    <div style={{ marginBottom: 4 }}>
                      <span className="badge" style={{ background: getMoodStyle(msg.mood).bg, color: getMoodStyle(msg.mood).text, border: `1px solid ${getMoodStyle(msg.mood).border}` }}>
                        {msg.mood}
                      </span>
                    </div>
                  )}
                  <div className={`chat-bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-friendly'}`}
                    style={msg.isError ? { background: 'var(--error)' } : {}}>
                    {msg.text}
                  </div>
                  {msg.role === 'bot' && !msg.isError && (
                    <div style={{ marginTop: 'var(--space-xs)' }}><TTSButton text={msg.text} size={14}/></div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-row chat-row-bot">
                <div className="chat-bubble bubble-friendly" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Loader2 size={16} style={{ animation: 'spin .8s linear infinite' }}/> Listening...
                </div>
              </div>
            )}
            <div ref={endRef}/>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border)', padding: 'var(--space-md)', display: 'flex', gap: 'var(--space-sm)' }}>
          <input type="text" className="input" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Tell me how you're feeling..." disabled={loading}
            style={{ flex: 1, minHeight: 44 }}/>
          <button className="btn" onClick={send} disabled={loading || !input.trim()}
            style={{ background: 'linear-gradient(135deg, var(--accent2), #F9A09A)', color: '#fff' }} aria-label="Send">
            <Send size={18}/>
          </button>
        </div>
      </div>
    </AppShell>
  );
}
