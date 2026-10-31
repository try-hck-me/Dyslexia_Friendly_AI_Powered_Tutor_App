'use client';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import {
  BookOpen, MessageCircle, Brain, Heart, BarChart3,
  Shield, ArrowRight, Sparkles, CheckCircle2, Network, Upload
} from 'lucide-react';

const features = [
  {
    icon: Upload,
    title: 'Upload & Process',
    desc: 'Upload PDFs in seconds. AI extracts, chunks, and indexes your notes automatically.',
    color: '#7C5CFC',
    badge: 'RAG Pipeline',
  },
  {
    icon: MessageCircle,
    title: 'Study Bot',
    desc: 'Ask questions from your notes in plain language. Get bullet-point answers, not walls of text.',
    color: '#6366F1',
    badge: 'Groq LLM',
  },
  {
    icon: Brain,
    title: 'Adaptive Quiz',
    desc: 'AI generates quizzes from your notes. Each question adapts to your knowledge level.',
    color: '#F5A623',
    badge: 'Auto-generated',
  },
  {
    icon: Heart,
    title: 'FriendlyBot',
    desc: 'Feeling stressed? FriendlyBot detects your mood and gives warm, personalised encouragement.',
    color: '#F47B6E',
    badge: 'Sentiment AI',
  },
  {
    icon: BarChart3,
    title: 'Progress Analytics',
    desc: 'Track weak topics, mood trends, quiz scores and get AI recommendations personalised for you.',
    color: '#4CAF82',
    badge: 'Live charts',
  },
  {
    icon: Shield,
    title: 'Parent Dashboard',
    desc: 'Parents can monitor their child\'s progress, mood trends and study activity — without pressure.',
    color: '#22D3EE',
    badge: 'Role-based',
  },
];

const trustItems = [
  'Lexend font — designed for dyslexic readers',
  'Adjustable font size, spacing & contrast',
  'Voice input & Text-to-Speech on every response',
  'Interactive Knowledge Graph',
  'SQLite-backed progress tracking',
  'Works 100% locally — your data stays on your device',
];

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh', overflowX: 'hidden' }}>

      {/* ── Navbar ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.9rem 2rem',
        background: scrolled ? 'rgba(253,246,236,0.92)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid var(--border)' : 'none',
        transition: 'all .3s ease',
        maxWidth: '100%',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1.6rem' }}>🧠</span>
          <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--accent)' }}>AI Tutor</span>
          <span style={{ fontSize: 'var(--fs-xs)', background: 'rgba(124,92,252,0.1)', color: 'var(--accent)', padding: '0.15rem 0.6rem', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>BTP 2026</span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Link href="/login" className="btn btn-secondary btn-sm">Sign In</Link>
          <Link href="/login" className="btn btn-primary btn-sm">Get Started <ArrowRight size={14}/></Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{ textAlign: 'center', padding: '5rem 2rem 4rem', maxWidth: 860, margin: '0 auto' }}>

        {/* Floating badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(124,92,252,0.08)', border: '1px solid rgba(124,92,252,0.2)',
          padding: '0.4rem 1.1rem', borderRadius: 'var(--radius-full)',
          fontSize: 'var(--fs-sm)', color: 'var(--accent)', fontWeight: 600,
          marginBottom: '1.5rem',
        }}>
          <Sparkles size={14}/> Dyslexia-Friendly · AI-Powered Learning
        </div>

        <h1 style={{
          fontSize: 'clamp(2.2rem, 6vw, 3.8rem)',
          fontWeight: 800, lineHeight: 1.12,
          marginBottom: '1.5rem', color: 'var(--text)',
        }}>
          Learning Made{' '}
          <span style={{
            background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            Easy
          </span>
          {' '}for Every Reader
        </h1>

        <p style={{
          fontSize: 'var(--fs-lg)', color: 'var(--text-secondary)',
          maxWidth: 620, margin: '0 auto 2.5rem', lineHeight: 1.8,
        }}>
          Upload your study notes, ask questions in simple language, take adaptive quizzes, and get emotional support — all in one dyslexia-friendly platform.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '3rem' }}>
          <Link href="/login" className="btn btn-primary btn-lg" style={{ boxShadow: '0 8px 28px rgba(124,92,252,0.35)' }}>
            Start Learning <ArrowRight size={18}/>
          </Link>
          <a href="#features" className="btn btn-secondary btn-lg">See Features</a>
        </div>

        {/* Hero mini-stats */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '2.5rem', flexWrap: 'wrap' }}>
          {[
            { num: '6+', label: 'AI Features' },
            { num: '100%', label: 'Local & Private' },
            { num: 'Lexend', label: 'Dyslexia Font' },
          ].map(({ num, label }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, color: 'var(--accent)' }}>{num}</div>
              <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it Works ── */}
      <section style={{ maxWidth: 960, margin: '0 auto', padding: '2rem 2rem 4rem' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
        }}>
          {[
            { step: '01', title: 'Upload PDF', desc: 'Drop any study PDF — textbook, notes, past papers.', icon: '📄' },
            { step: '02', title: 'AI Processes', desc: 'Content is chunked, embedded and indexed instantly.', icon: '⚙️' },
            { step: '03', title: 'Learn Your Way', desc: 'Chat, quiz, or read with full accessibility controls.', icon: '🎓' },
            { step: '04', title: 'Track Progress', desc: 'See analytics, weak topics and mood trends.', icon: '📊' },
          ].map(({ step, title, desc, icon }) => (
            <div key={step} style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)', padding: '1.5rem',
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{ position: 'absolute', top: 12, right: 16, fontSize: 'var(--fs-xs)', fontWeight: 800, color: 'rgba(124,92,252,0.15)', letterSpacing: '0.04em' }}>{step}</div>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{icon}</div>
              <div style={{ fontWeight: 700, marginBottom: '0.4rem' }}>{title}</div>
              <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features Grid ── */}
      <section id="features" style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 2rem 5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, marginBottom: '0.5rem' }}>Everything You Need to Learn Better</h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: 500, margin: '0 auto' }}>
            Six AI-powered tools, designed specifically for dyslexic students and their parents.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {features.map(({ icon: Icon, title, desc, color, badge }) => (
            <div key={title} className="card" style={{ padding: '1.75rem', cursor: 'default', position: 'relative', overflow: 'hidden' }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = 'var(--shadow-lg)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
              {/* Background accent */}
              <div style={{ position: 'absolute', top: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: `${color}10` }}/>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={24} color={color}/>
                </div>
                <span style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, background: `${color}12`, color, padding: '0.2rem 0.6rem', borderRadius: 'var(--radius-full)', border: `1px solid ${color}25` }}>
                  {badge}
                </span>
              </div>
              <h3 style={{ fontSize: 'var(--fs-lg)', fontWeight: 700, marginBottom: '0.5rem' }}>{title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-sm)', lineHeight: 1.7, margin: 0 }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Accessibility Trust Strip ── */}
      <section style={{ background: 'linear-gradient(135deg, rgba(124,92,252,0.06), rgba(244,123,110,0.04))', padding: '3rem 2rem', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: 'var(--fs-xl)', fontWeight: 800, marginBottom: '0.5rem' }}>Built for Accessibility</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>Every design decision was made with dyslexic readers in mind.</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
            {trustItems.map(item => (
              <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>
                <CheckCircle2 size={16} color="var(--success)" style={{ flexShrink: 0 }}/>
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ textAlign: 'center', padding: '5rem 2rem' }}>
        <div style={{
          display: 'inline-block',
          background: 'linear-gradient(135deg, rgba(124,92,252,0.06), rgba(244,123,110,0.04))',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)', padding: '3rem 4rem',
          maxWidth: 600,
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🚀</div>
          <h2 style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, marginBottom: '1rem' }}>Ready to Start?</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', lineHeight: 1.7 }}>
            Upload your first PDF and let AI make studying easier, clearer, and more enjoyable.
          </p>
          <Link href="/login" className="btn btn-primary btn-lg"
            style={{ boxShadow: '0 8px 28px rgba(124,92,252,0.35)' }}>
            Create Free Account <ArrowRight size={18}/>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ textAlign: 'center', padding: '1.5rem 2rem', borderTop: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
        <p>Built with ❤️ for dyslexic learners • BTP Project 2026</p>
      </footer>
    </div>
  );
}
