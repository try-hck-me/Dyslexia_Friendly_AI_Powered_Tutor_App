'use client';
import AppShell from '@/components/layout/AppShell';
import { useUser } from '@/context/UserContext';
import { useEffect, useState, useRef } from 'react';
import { getAnalytics } from '@/lib/api';
import { TrendingDown, Sparkles, RefreshCw, BarChart3, Smile, BookOpen } from 'lucide-react';
import { MOOD_COLORS } from '@/lib/constants';

/* ── Tiny Chart helpers (no import issues on SSR) ──────── */
function DonutChart({ segments, size = 140 }) {
  const r = 46, cx = 70, cy = 70;
  const circumference = 2 * Math.PI * r;
  let offset = 0;
  const total = segments.reduce((s, seg) => s + seg.value, 0) || 1;
  return (
    <svg width={size} height={size} viewBox="0 0 140 140">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-alt)" strokeWidth={20}/>
      {segments.map((seg, i) => {
        const dash = (seg.value / total) * circumference;
        const el = (
          <circle key={i} cx={cx} cy={cy} r={r}
            fill="none" stroke={seg.color} strokeWidth={20}
            strokeDasharray={`${dash} ${circumference - dash}`}
            strokeDashoffset={-offset}
            strokeLinecap="round"
            style={{ transform: 'rotate(-90deg)', transformOrigin: '70px 70px', transition: 'stroke-dasharray .6s ease' }}
          />
        );
        offset += dash;
        return el;
      })}
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize={22} fontWeight={800} fill="var(--accent)">
        {total}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fontSize={9} fill="var(--text-muted)" fontWeight={600} letterSpacing="1">
        SESSIONS
      </text>
    </svg>
  );
}

function BarChart({ bars, maxVal }) {
  const max = maxVal || Math.max(...bars.map(b => b.value), 1);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 120, padding: '0 4px' }}>
      {bars.map((bar, i) => (
        <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, height: '100%', justifyContent: 'flex-end' }}>
          <span style={{ fontSize: 9, fontWeight: 700, color: bar.color || 'var(--accent)' }}>{bar.value}%</span>
          <div style={{ width: '100%', borderRadius: '4px 4px 0 0', background: bar.color || 'var(--accent)', height: `${(bar.value / max) * 85}%`, minHeight: 4, opacity: 0.85, transition: 'height .5s ease' }}/>
          <span style={{ fontSize: 8, color: 'var(--text-muted)', textTransform: 'capitalize', textAlign: 'center', lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', maxWidth: '100%', textOverflow: 'ellipsis' }}>{bar.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const { effectiveUserId, role } = useUser();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = (isInitial = false) => {
    if (!effectiveUserId) return;
    if (isInitial) {
      setLoading(true);
      setError('');
    }
    getAnalytics(effectiveUserId)
      .then(res => { if (res.success) setData(res.data); else if (isInitial) setError('Could not load analytics.'); })
      .catch(err => { if (isInitial) setError(err.message); })
      .finally(() => { if (isInitial) setLoading(false); });
  };

  useEffect(() => {
    load(true);
    const interval = setInterval(() => load(false), 5000);
    return () => clearInterval(interval);
  }, [effectiveUserId]);

  if (loading) return <AppShell><div className="flex-center" style={{ padding: '4rem' }}><div className="spinner"/></div></AppShell>;
  if (error)   return <AppShell><div className="error-box" style={{ margin: '2rem' }}>{error}<button className="btn btn-sm btn-secondary" onClick={load} style={{ marginLeft: 12 }}>Retry</button></div></AppShell>;
  if (!data)   return <AppShell><div className="empty-state"><p className="empty-text">No data yet. Start using the app to see your progress!</p></div></AppShell>;

  const stats      = data.study_stats    || {};
  const allTopics  = data.all_topics     || [];
  const weak       = data.weak_topics    || [];
  const mood       = data.mood_trends    || {};
  const recs       = data.recommendations|| [];
  const moodCounts = mood.counts         || {};
  const totalMoods = mood.total          || 0;

  // Donut segments for mood distribution
  const moodSegments = Object.entries(moodCounts)
    .filter(([, v]) => v > 0)
    .map(([m, count]) => ({
      label: m, value: count,
      color: (MOOD_COLORS[m] || MOOD_COLORS.neutral)?.border || '#7C5CFC',
    }));

  // Bar chart — all topics colour-coded by score band
  const topicBars = allTopics.slice(0, 8).map(t => ({
    label: t.topic,
    value: t.avg_score,
    color: t.avg_score < 40 ? 'var(--error)'
         : t.avg_score < 70 ? 'var(--warning)'
         : 'var(--success)',
  }));

  return (
    <AppShell>
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">{role === 'parent' ? "Child's Progress 📊" : 'My Progress 📊'}</h1>
          <p className="page-subtitle">Track your learning journey, weak areas, and mood trends.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load} title="Refresh">
          <RefreshCw size={16}/> Refresh
        </button>
      </div>

      {/* ── Stat Cards ── */}
      <div className="grid-3" style={{ marginBottom: 'var(--space-2xl)' }}>
        {[
          { icon: BookOpen, label: 'Questions Asked',  value: stats.questions_asked  || 0, color: '#7C5CFC' },
          { icon: BarChart3, label: 'Quizzes Taken',   value: stats.quizzes_taken    || 0, color: '#F47B6E' },
          { icon: Smile,    label: 'Avg Quiz Score',   value: `${stats.avg_quiz_score || 0}%`, color: '#4CAF82' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="card stat-card" style={{ position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -8, right: -8, width: 64, height: 64, borderRadius: '50%', background: `${color}12` }}/>
            <Icon size={22} color={color} style={{ marginBottom: 8 }}/>
            <div className="stat-value" style={{ fontSize: 'var(--fs-3xl)' }}>{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* ── Charts Row ── */}
      <div className="grid-2" style={{ marginBottom: 'var(--space-2xl)' }}>

        {/* All Topics Bar Chart */}
        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-lg)', fontSize: 'var(--fs-base)' }}>
            <TrendingDown size={18} color="var(--accent2)"/> Topic Performance
          </h3>
          {topicBars.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>No quiz data yet. Take some quizzes!</p>
          ) : (
            <>
              <BarChart bars={topicBars} maxVal={100}/>
              <div style={{ marginTop: 12, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {[
                  { color: 'var(--error)',   label: 'Needs work (<40%)' },
                  { color: 'var(--warning)', label: 'Fair (40–70%)' },
                  { color: 'var(--success)', label: 'Good (≥70%)' },
                ].map(({ color, label }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 9, color: 'var(--text-muted)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: color }}/>
                    {label}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Mood Donut Chart */}
        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-lg)', fontSize: 'var(--fs-base)' }}>
            <Smile size={18} color="var(--accent)"/> Mood Distribution
          </h3>
          {totalMoods === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>No mood data yet. Chat with FriendlyBot!</p>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xl)' }}>
              <DonutChart segments={moodSegments}/>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {moodSegments.sort((a, b) => b.value - a.value).slice(0, 5).map(seg => (
                  <div key={seg.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: seg.color, flexShrink: 0 }}/>
                    <span style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, textTransform: 'capitalize', color: 'var(--text-secondary)', flex: 1 }}>{seg.label}</span>
                    <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>{Math.round((seg.value / totalMoods) * 100)}%</span>
                  </div>
                ))}
                <div style={{ marginTop: 4, fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                  Dominant: <strong style={{ color: 'var(--text)', textTransform: 'capitalize' }}>{mood.dominant_mood || 'neutral'}</strong>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── All Topics Detail List ── */}
      {allTopics.length > 0 && (
        <div className="card" style={{ padding: 'var(--space-xl)', marginBottom: 'var(--space-2xl)' }}>
          <h3 style={{ marginBottom: 'var(--space-lg)', fontSize: 'var(--fs-base)' }}>📋 Topic Breakdown</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {allTopics.map((t, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-sm)', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{t.topic}</span>
                  <div style={{ display: 'flex', gap: 12, color: 'var(--text-muted)', fontSize: 'var(--fs-xs)' }}>
                    <span>{t.attempts} attempt{t.attempts !== 1 ? 's' : ''}</span>
                    <span style={{ fontWeight: 700, color: t.avg_score < 40 ? 'var(--error)' : t.avg_score < 70 ? 'var(--warning)' : 'var(--success)' }}>
                      {t.avg_score}%
                    </span>
                  </div>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{
                    width: `${t.avg_score}%`,
                    background: t.avg_score < 40 ? 'var(--error)' : t.avg_score < 70 ? 'var(--warning)' : 'var(--success)'
                  }}/>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommendations ── */}
      {recs.length > 0 && (
        <div>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-md)' }}>
            <Sparkles size={20} color="var(--accent)"/> AI Recommendations
          </h3>
          <div className="grid-2">
            {recs.map((r, i) => (
              <div key={i} className="card card-accent" style={{ padding: 'var(--space-md) var(--space-lg)', fontSize: 'var(--fs-sm)' }}>
                <span style={{ marginRight: 8 }}>💡</span>{r}
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
