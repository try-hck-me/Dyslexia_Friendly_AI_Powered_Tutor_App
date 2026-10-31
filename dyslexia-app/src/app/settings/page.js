'use client';
import AppShell from '@/components/layout/AppShell';
import { useAccessibility } from '@/context/AccessibilityContext';
import { useUser } from '@/context/UserContext';
import { TTS_VOICES } from '@/lib/constants';
import { RotateCcw, Copy, Check } from 'lucide-react';
import { useState } from 'react';

export default function SettingsPage() {
  const a11y = useAccessibility();
  const { userId, name, role, dispatch } = useUser();
  const [copied, setCopied] = useState(false);

  const copyId = () => {
    navigator.clipboard.writeText(userId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">Settings ⚙️</h1>
        <p className="page-subtitle">Customize your reading experience and accessibility preferences.</p>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Reading Preferences */}
        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          <h3 style={{ marginBottom: 'var(--space-lg)' }}>📖 Reading Preferences</h3>

          <div className="input-group">
            <label htmlFor="fontFamily">Website Font</label>
            <select id="fontFamily" className="select" value={a11y.fontFamily || 'normal'} onChange={e => a11y.set('fontFamily', e.target.value)}>
              <option value="normal">Lexend (Default)</option>
              <option value="opendyslexic">OpenDyslexic</option>
              <option value="atkinson">Atkinson Hyperlegible</option>
            </select>
          </div>

          <div className="input-group">
            <label>Font Size: {a11y.fontSize.toFixed(2)}rem</label>
            <input type="range" min="0.875" max="1.5" step="0.0625" value={a11y.fontSize}
              onChange={e => a11y.set('fontSize', +e.target.value)}
              style={{ width: '100%', accentColor: 'var(--accent)' }}/>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
              <span>Smaller</span><span>Larger</span>
            </div>
          </div>

          <div className="input-group">
            <label>Line Spacing: {a11y.lineHeight.toFixed(1)}</label>
            <input type="range" min="1.4" max="2.5" step="0.1" value={a11y.lineHeight}
              onChange={e => a11y.set('lineHeight', +e.target.value)}
              style={{ width: '100%', accentColor: 'var(--accent)' }}/>
          </div>

          <div className="input-group">
            <label>Letter Spacing: {a11y.letterSpacing.toFixed(2)}em</label>
            <input type="range" min="0" max="0.12" step="0.01" value={a11y.letterSpacing}
              onChange={e => a11y.set('letterSpacing', +e.target.value)}
              style={{ width: '100%', accentColor: 'var(--accent)' }}/>
          </div>

          <button className="btn btn-ghost btn-sm" onClick={a11y.reset} style={{ marginTop: 'var(--space-sm)' }}>
            <RotateCcw size={14}/> Reset to Defaults
          </button>
        </div>

        {/* Voice & Profile */}
        <div className="flex-col" style={{ gap: 'var(--space-lg)' }}>
          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>🔊 Voice Settings</h3>
            <div className="input-group">
              <label htmlFor="voice">Read Aloud Voice</label>
              <select id="voice" className="select" value={a11y.ttsVoice} onChange={e => a11y.set('ttsVoice', e.target.value)}>
                {TTS_VOICES.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
              </select>
            </div>
          </div>

          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>👤 Profile</h3>
            <div className="input-group">
              <label htmlFor="userName">Display Name</label>
              <input id="userName" className="input" value={name} onChange={e => dispatch({ type: 'LOGIN', payload: { name: e.target.value } })}/>
            </div>
            <div className="input-group">
              <label>Your Student ID</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input className="input" value={userId} readOnly style={{ flex: 1, background: 'var(--bg-alt)' }}/>
                <button className="btn btn-ghost" onClick={copyId} title="Copy ID">
                  {copied ? <Check size={16} color="var(--success)"/> : <Copy size={16}/>}
                </button>
              </div>
              <small style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-xs)' }}>
                {role === 'student' ? 'Share this ID with your parent so they can view your progress.' : "This is your parent account ID."}
              </small>
            </div>
          </div>

          {/* Live Preview */}
          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-md)' }}>👁️ Live Preview</h3>
            <div style={{ fontSize: `${a11y.fontSize}rem`, lineHeight: a11y.lineHeight, letterSpacing: `${a11y.letterSpacing}em`, fontFamily: 'var(--font-primary)', padding: 'var(--space-md)', background: 'var(--bg-alt)', borderRadius: 'var(--radius-md)' }}>
              <p style={{ marginBottom: '0.5rem' }}>This is how your text will look.</p>
              <p>A cell is the smallest unit of life. All living things are made of cells. Some have one cell, others have many.</p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
