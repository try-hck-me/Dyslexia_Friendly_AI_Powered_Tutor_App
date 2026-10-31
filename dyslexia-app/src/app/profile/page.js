'use client';
import AppShell from '@/components/layout/AppShell';
import { useUser } from '@/context/UserContext';
import { getAnalytics } from '@/lib/api';
import { useEffect, useState } from 'react';
import {
  UserCircle, Copy, Check, BookOpen, Brain, BarChart3,
  Flame, ClipboardList, Users, Edit3, Save, X, Badge,
  GraduationCap, HeartHandshake,
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, color = 'var(--accent)' }) {
  return (
    <div className="card" style={{ padding: 'var(--space-lg)', display: 'flex', alignItems: 'center', gap: 'var(--space-md)', flex: 1, minWidth: 140 }}>
      <div style={{
        width: 48, height: 48, borderRadius: 'var(--radius-md)',
        background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, color, lineHeight: 1 }}>{value ?? '—'}</div>
        <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      </div>
    </div>
  );
}

function CopyField({ label, value, hint }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="input-group">
      <label>{label}</label>
      <div style={{ display: 'flex', gap: 8 }}>
        <input className="input" value={value} readOnly style={{ flex: 1, background: 'var(--bg-alt)', fontFamily: 'monospace', fontSize: 'var(--fs-sm)' }} />
        <button className="btn btn-ghost" onClick={copy} title="Copy" style={{ flexShrink: 0 }}>
          {copied ? <Check size={16} color="var(--success)" /> : <Copy size={16} />}
        </button>
      </div>
      {hint && <small style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-xs)' }}>{hint}</small>}
    </div>
  );
}

export default function ProfilePage() {
  const { userId, name, role, parentLinkedStudentId, effectiveUserId, dispatch } = useUser();
  const [analytics, setAnalytics] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [editing, setEditing] = useState(false);
  const [draftName, setDraftName] = useState(name);

  useEffect(() => { setDraftName(name); }, [name]);

  useEffect(() => {
    if (!effectiveUserId) { setLoadingStats(false); return; }
    
    const fetchStats = () => {
      getAnalytics(effectiveUserId)
        .then(res => { if (res.success) setAnalytics(res.data); })
        .catch(() => {})
        .finally(() => setLoadingStats(false));
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [effectiveUserId]);

  const saveName = () => {
    if (draftName.trim()) {
      dispatch({ type: 'LOGIN', payload: { name: draftName.trim() } });
    }
    setEditing(false);
  };

  const initials = (name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  const isParent = role === 'parent';
  const stats = analytics?.study_stats || {};

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">My Profile 👤</h1>
        <p className="page-subtitle">Your account information and learning stats at a glance.</p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-xl)', alignItems: 'flex-start', flexWrap: 'wrap' }}>

        {/* ── Left: Avatar + Identity Card ────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)', width: 300, flexShrink: 0 }}>
          <div className="card" style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
            {/* Avatar */}
            <div style={{
              width: 96, height: 96, borderRadius: '50%', margin: '0 auto var(--space-md)',
              background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2rem', fontWeight: 800, color: '#fff',
              boxShadow: '0 8px 24px rgba(124,92,252,0.35)',
            }}>
              {initials}
            </div>

            {/* Name display / edit */}
            {editing ? (
              <div style={{ display: 'flex', gap: 8, marginBottom: 'var(--space-sm)' }}>
                <input
                  className="input"
                  value={draftName}
                  onChange={e => setDraftName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') saveName(); if (e.key === 'Escape') setEditing(false); }}
                  autoFocus
                  style={{ textAlign: 'center', flex: 1 }}
                />
                <button className="btn btn-ghost btn-sm" onClick={saveName} title="Save"><Save size={14} /></button>
                <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)} title="Cancel"><X size={14} /></button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 'var(--space-sm)' }}>
                <h2 style={{ margin: 0, fontSize: 'var(--fs-xl)', color: 'var(--text-primary)' }}>{name || 'User'}</h2>
                <button className="btn-icon" onClick={() => setEditing(true)} title="Edit name" style={{ opacity: 0.5 }}>
                  <Edit3 size={14} />
                </button>
              </div>
            )}

            {/* Role badge */}
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: isParent ? 'rgba(249,168,37,0.12)' : 'rgba(124,92,252,0.12)',
              color: isParent ? '#F9A825' : 'var(--accent)',
              border: `1px solid ${isParent ? '#F9A82544' : 'rgba(124,92,252,0.3)'}`,
              borderRadius: 20, padding: '4px 14px', fontSize: 'var(--fs-sm)', fontWeight: 700,
            }}>
              {isParent ? <HeartHandshake size={14} /> : <GraduationCap size={14} />}
              {isParent ? 'Parent Account' : 'Student Account'}
            </div>
          </div>

          {/* IDs card */}
          <div className="card" style={{ padding: 'var(--space-lg)' }}>
            <h3 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>🔑 Account IDs</h3>
            <CopyField
              label={isParent ? 'Parent Account ID' : 'Student ID'}
              value={userId}
              hint={!isParent ? 'Share with your parent so they can track your progress.' : undefined}
            />
            {isParent && parentLinkedStudentId && (
              <CopyField
                label="Linked Student ID"
                value={parentLinkedStudentId}
                hint="Your child's account you are tracking."
              />
            )}
          </div>
        </div>

        {/* ── Right: Stats + Activity ─────────────────────── */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>

          {/* Stats row */}
          <div>
            <h3 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)', color: 'var(--text-secondary)' }}>
              {isParent ? "📊 Child's Learning Stats" : '📊 Your Learning Stats'}
            </h3>
            {loadingStats ? (
              <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="card" style={{ flex: 1, minWidth: 140, height: 88, background: 'var(--bg-alt)', animation: 'pulse 1.5s infinite' }} />
                ))}
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
                <StatCard icon={ClipboardList} label="Quizzes Taken"   value={stats.total_quizzes}       color="#7C5CFC" />
                <StatCard icon={BookOpen}     label="Docs Uploaded"    value={stats.total_documents}      color="#4A9FFF" />
                <StatCard icon={Flame}        label="Day Streak"       value={stats.streak_days ?? 0}     color="#F47B6E" />
                <StatCard icon={BarChart3}    label="Avg Score"        value={stats.average_score != null ? `${Math.round(stats.average_score)}%` : '—'} color="#4CAF82" />
              </div>
            )}
          </div>

          {/* Weak topics */}
          {!loadingStats && analytics?.weak_topics?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-lg)' }}>
              <h3 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>🎯 Topics to Revisit</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {analytics.weak_topics.map((t, i) => (
                  <span key={i} style={{
                    background: 'rgba(244,123,110,0.10)', color: '#F47B6E',
                    border: '1px solid rgba(244,123,110,0.25)',
                    borderRadius: 20, padding: '4px 14px', fontSize: 'var(--fs-xs)', fontWeight: 600,
                  }}>{t.topic}</span>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {!loadingStats && analytics?.recommendations?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-lg)' }}>
              <h3 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>💡 Recommendations</h3>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {analytics.recommendations.slice(0, 5).map((r, i) => (
                  <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <span style={{ color: 'var(--accent)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Empty state if no analytics at all */}
          {!loadingStats && !analytics && (
            <div className="card" style={{ padding: 'var(--space-2xl)', textAlign: 'center' }}>
              <Brain size={48} color="var(--accent)" style={{ opacity: 0.25, marginBottom: 12 }} />
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
                No learning activity yet. Upload a PDF and take a quiz to see your stats here!
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
