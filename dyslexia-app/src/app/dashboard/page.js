'use client';
import AppShell from '@/components/layout/AppShell';
import { useUser } from '@/context/UserContext';
import { useEffect, useState } from 'react';
import { getAnalytics } from '@/lib/api';
import Link from 'next/link';
import {
  Upload, MessageCircle, Brain, Heart, BarChart3,
  Sparkles, BookOpen, Network, TrendingUp, Smile,
  ArrowRight, Star
} from 'lucide-react';

/* ── Progress Ring ── */
function ProgressRing({ pct, size = 80, stroke = 8, color = 'var(--accent)' }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (pct / 100) * circ;
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--bg-alt)" strokeWidth={stroke}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={stroke}
        strokeDasharray={`${filled} ${circ - filled}`} strokeLinecap="round"
        style={{ transition: 'stroke-dasharray .8s ease' }}/>
    </svg>
  );
}

const MOOD_EMOJI = { joy: '😊', sadness: '😢', anger: '😠', fear: '😰', neutral: '😐', surprise: '😲', disgust: '😕' };
const GREETINGS  = ['Ready to learn?', 'Keep it up!', 'Every step counts!', 'You\'re doing great!'];

const ALL_ACTIONS = [
  { href: '/documents', icon: Upload,        label: 'Upload Notes',  desc: 'Add new study material',      color: '#7C5CFC', roles: ['student','parent'] },
  { href: '/chat',      icon: MessageCircle, label: 'Study Bot',     desc: 'Ask questions from your notes', color: '#6366F1', roles: ['student'] },
  { href: '/quiz',      icon: Brain,         label: 'Take a Quiz',   desc: 'Test your knowledge',          color: '#F5A623', roles: ['student'] },
  { href: '/friendly',  icon: Heart,         label: 'FriendlyBot',   desc: 'Talk about how you feel',      color: '#F47B6E', roles: ['student'] },
  { href: '/reader',    icon: BookOpen,      label: 'PDF Reader',    desc: 'Read in accessible mode',      color: '#4CAF82', roles: ['student'] },
  { href: '/analytics', icon: BarChart3,     label: 'Progress',      desc: 'View analytics dashboard',     color: '#22D3EE', roles: ['student','parent'] },
  { href: '/graph',     icon: Network,       label: 'Knowledge Map', desc: 'Visual concept graph',         color: '#A855F7', roles: ['student','parent'] },
];

export default function DashboardPage() {
  const { name, role, effectiveUserId } = useUser();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  // useState initializer only runs on client — avoids SSR/client Date.now() mismatch
  const [greeting] = useState(() => GREETINGS[Math.floor(Date.now() / 3600000) % GREETINGS.length]);

  useEffect(() => {
    if (!effectiveUserId) return;
    
    const fetchAnalytics = () => {
      getAnalytics(effectiveUserId)
        .then(res => { if (res.success) setAnalytics(res.data); })
        .catch(() => {})
        .finally(() => setLoading(false));
    };

    fetchAnalytics();
    // Poll every 5 seconds for real-time progress updates (especially for parents)
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, [effectiveUserId]);

  const stats   = analytics?.study_stats    || { questions_asked: 0, quizzes_taken: 0, avg_quiz_score: 0 };
  const recs    = analytics?.recommendations|| [];
  const mood    = analytics?.mood_trends    || {};
  const weak    = analytics?.weak_topics    || [];
  const domMood = mood.dominant_mood || 'neutral';
  const actions = ALL_ACTIONS.filter(a => a.roles.includes(role || 'student'));

  return (
    <AppShell>
      {/* ── Hero Welcome ── */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(124,92,252,0.08), rgba(244,123,110,0.06))',
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-xl) var(--space-2xl)',
        marginBottom: 'var(--space-2xl)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 'var(--space-lg)',
      }}>
        <div>
          <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent)', marginBottom: 6 }}>
            {role === 'parent' ? 'Parent Dashboard' : 'Student Dashboard'}
          </div>
          <h1 style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, color: 'var(--text)', marginBottom: 4 }}>
            {role === 'parent' ? `Welcome, ${name}` : `Hi, ${name || 'Student'}`}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', margin: 0 }}>
            {role === 'parent' ? `Viewing progress for Student ID: ${effectiveUserId}` : greeting}
          </p>
        </div>

        {/* Mood & Score ring */}
        <div style={{ display: 'flex', gap: 'var(--space-xl)', alignItems: 'center' }}>
          {domMood && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem' }}>{MOOD_EMOJI[domMood] || '😐'}</div>
              <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', textTransform: 'capitalize', marginTop: 4 }}>{domMood}</div>
            </div>
          )}
          <div style={{ position: 'relative', width: 80, height: 80 }}>
            <ProgressRing pct={stats.avg_quiz_score || 0}
              color={stats.avg_quiz_score >= 70 ? 'var(--success)' : stats.avg_quiz_score >= 40 ? 'var(--warning)' : 'var(--accent)'}/>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
              <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 800, color: 'var(--text)', lineHeight: 1 }}>{stats.avg_quiz_score || 0}%</span>
              <span style={{ fontSize: 7, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>score</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="grid-3" style={{ marginBottom: 'var(--space-2xl)' }}>
        {[
          { icon: MessageCircle, label: 'Questions Asked', value: stats.questions_asked, color: '#7C5CFC' },
          { icon: Brain,         label: 'Quizzes Taken',   value: stats.quizzes_taken,   color: '#F47B6E' },
          { icon: TrendingUp,    label: 'Average Score',   value: `${stats.avg_quiz_score}%`, color: '#4CAF82' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="card stat-card" style={{ position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -10, right: -10, width: 70, height: 70, borderRadius: '50%', background: `${color}10` }}/>
            <Icon size={20} color={color} style={{ marginBottom: 6 }}/>
            <div className="stat-value">{loading ? '—' : value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* ── Recs + Weak Topics Side-by-side ── */}
      {(recs.length > 0 || weak.length > 0) && (
        <div className="grid-2" style={{ marginBottom: 'var(--space-2xl)' }}>
          {recs.length > 0 && (
            <div>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>
                <Sparkles size={18} color="var(--accent)"/> Today's Tips
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {recs.slice(0, 3).map((r, i) => (
                  <div key={i} className="card" style={{ padding: 'var(--space-md)', display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 'var(--fs-sm)', borderLeft: '3px solid var(--accent)' }}>
                    <Star size={14} color="var(--accent)" style={{ marginTop: 3, flexShrink: 0 }}/>
                    {r}
                  </div>
                ))}
              </div>
            </div>
          )}

          {weak.length > 0 && (
            <div>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>
                <TrendingUp size={18} color="var(--accent2)"/> Focus Areas
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {weak.slice(0, 3).map((t, i) => (
                  <div key={i} className="card" style={{ padding: 'var(--space-sm) var(--space-md)', borderLeft: '3px solid var(--accent2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-sm)', marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{t.topic}</span>
                      <span style={{ color: t.avg_score < 40 ? 'var(--error)' : 'var(--warning)', fontWeight: 700 }}>{t.avg_score}%</span>
                    </div>
                    <div className="progress-track" style={{ height: 5 }}>
                      <div className="progress-fill" style={{ width: `${t.avg_score}%`, background: t.avg_score < 40 ? 'var(--error)' : 'var(--warning)' }}/>
                    </div>
                  </div>
                ))}
                <Link href="/analytics" className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start' }}>
                  View full analytics <ArrowRight size={14}/>
                </Link>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Quick Actions Grid ── */}
      <h3 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--fs-base)' }}>Quick Actions</h3>
      <div className="grid-3">
        {actions.map(({ href, icon: Icon, label, desc, color }) => (
          <Link key={href} href={href} style={{ textDecoration: 'none' }}>
            <div className="card" style={{ padding: 'var(--space-lg)', cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: 'var(--space-md)', transition: 'all .2s' }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-lg)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
              <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon size={22} color={color}/>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 700, color: 'var(--text)', marginBottom: 2, fontSize: 'var(--fs-sm)' }}>{label}</div>
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: 1.4 }}>{desc}</div>
              </div>
              <ArrowRight size={16} color={color} style={{ opacity: 0.5, flexShrink: 0, marginTop: 2 }}/>
            </div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
