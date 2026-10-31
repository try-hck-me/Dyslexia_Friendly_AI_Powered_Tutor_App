'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@/context/UserContext';
import { registerUser, getUser } from '@/lib/api';
import { GraduationCap, Users, ArrowRight, Eye, EyeOff, Loader2, CheckCircle } from 'lucide-react';

/**
 * Generates a deterministic, URL-safe user ID from a name.
 * e.g. "Prashil Kagathara" → "prashil_kagathara"
 */
function makeUserId(name) {
  if (!name) return '';
  return name.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
}

export default function LoginPage() {
  const [mode, setMode]           = useState('login');   // 'login' | 'signup'
  const [role, setRole]           = useState('');        // 'student' | 'parent'
  const [name, setName]           = useState('');
  const [childId, setChildId]     = useState('');
  const [showPwd, setShowPwd]     = useState(false);
  const [password, setPassword]   = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]         = useState('');
  const [childName, setChildName] = useState('');        // resolved name after ID lookup

  const { login, isLoggedIn, isInitialized } = useUser();
  const router    = useRouter();

  useEffect(() => {
    if (isInitialized && isLoggedIn) {
      router.push('/dashboard');
    }
  }, [isLoggedIn, isInitialized, router]);

  /* ── Child ID lookup (parents only) ── */
  const handleChildIdBlur = async () => {
    const id = childId.trim();
    if (!id || role !== 'parent') return;
    try {
      const res = await getUser(id);
      if (res.success && res.data.exists) {
        setChildName(res.data.name);
        setError('');
      } else {
        setChildName('');
      }
    } catch {
      // Backend unreachable — don't block login
      setChildName('');
    }
  };

  /* ── Form submit ── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (!role)        { setError('Please select Student or Parent.'); return; }
    if (!name.trim()) { setError('Please enter your name.'); return; }
    if (role === 'parent' && !childId.trim()) {
      setError("Please enter your child's Student ID."); return;
    }

    setSubmitting(true);

    try {
      const userId = makeUserId(name);

      if (mode === 'login') {
        // ── SIGN IN: user must already exist ──
        let checkId = userId;
        if (role === 'parent') checkId = childId.trim(); // parent logs in with their own generated ID

        try {
          const check = await getUser(role === 'parent' ? `parent_${makeUserId(name)}` : userId);
          if (!check.success || !check.data.exists) {
            setError("No account found with that name. Please Sign Up first.");
            setSubmitting(false);
            return;
          }
        } catch {
          // Backend offline — allow login anyway (localStorage fallback)
        }

        // For parents, verify the child ID exists
        if (role === 'parent' && childId.trim()) {
          try {
            const childCheck = await getUser(childId.trim());
            if (childCheck.success && !childCheck.data.exists) {
              setError("Child's Student ID not found. Ask your child to Sign Up first.");
              setSubmitting(false);
              return;
            }
          } catch {}
        }

      } else {
        // ── SIGN UP: user must NOT already exist ──
        const newUserId = role === 'parent' ? `parent_${userId}` : userId;
        // For parents, verify the child ID exists BEFORE signup
        if (role === 'parent' && childId.trim()) {
          try {
            const childCheck = await getUser(makeUserId(childId));
            if (childCheck.success && !childCheck.data.exists) {
              setError("Child's Student ID not found. Your child must Sign Up first.");
              setSubmitting(false);
              return;
            }
          } catch {}
        }

        try {
          const check = await getUser(newUserId);
          if (check.success && check.data.exists) {
            setError("An account with that name already exists. Please Sign In instead.");
            setSubmitting(false);
            return;
          }
        } catch {
          // Backend offline — proceed with creation
        }

        // Register the new user in SQLite
        try {
          await registerUser(newUserId, name.trim(), role);
        } catch {
          console.warn('Could not register in DB — using local session only.');
        }
      }

      // Build the final userId for session
      const finalUserId = role === 'parent' ? `parent_${userId}` : userId;
      const finalChildId = role === 'parent' ? makeUserId(childId) : '';
      login(finalUserId, name.trim(), role, finalChildId);
      router.push('/dashboard');

    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => { setMode(m => m === 'login' ? 'signup' : 'login'); setError(''); };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, var(--bg) 0%, #F0EAFF 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '2rem',
    }}>
      <div style={{ width: '100%', maxWidth: 480 }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🧠</div>
          <h1 style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, marginBottom: '0.25rem' }}>
            {mode === 'login' ? 'Welcome Back!' : 'Create Account'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
            {mode === 'login' ? 'Sign in to continue your learning journey.' : 'Join and start learning in a dyslexia-friendly way.'}
          </p>
        </div>

        <div className="card" style={{ padding: '2rem', boxShadow: 'var(--shadow-lg)' }}>

          {/* ── Role Selector ── */}
          {!role && (
            <div>
              <p style={{ fontWeight: 700, marginBottom: 'var(--space-md)', textAlign: 'center', fontSize: 'var(--fs-base)' }}>
                I am a…
              </p>
              <div className="grid-2" style={{ gap: '1rem' }}>
                {[
                  { value: 'student', Icon: GraduationCap, label: 'Student', desc: 'I want to learn', color: 'var(--accent)' },
                  { value: 'parent',  Icon: Users,          label: 'Parent',  desc: 'Monitor progress', color: 'var(--accent2)' },
                ].map(({ value, Icon, label, desc, color }) => (
                  <button key={value} onClick={() => { setRole(value); setError(''); }}
                    style={{
                      background: 'var(--bg-card)', border: `2px solid var(--border)`,
                      borderRadius: 'var(--radius-lg)', padding: '1.5rem',
                      textAlign: 'center', cursor: 'pointer', transition: 'all .2s',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = color; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = ''; }}>
                    <Icon size={36} color={color}/>
                    <div style={{ fontWeight: 700, fontSize: 'var(--fs-base)' }}>{label}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>{desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── Login / Signup Form ── */}
          {role && (
            <form onSubmit={handleSubmit}>

              {/* Role badge with change button */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                marginBottom: 'var(--space-lg)', padding: '0.5rem 1rem',
                background: role === 'parent' ? 'rgba(244,123,110,0.08)' : 'rgba(124,92,252,0.08)',
                borderRadius: 'var(--radius-md)',
              }}>
                {role === 'student'
                  ? <GraduationCap size={16} color="var(--accent)"/>
                  : <Users size={16} color="var(--accent2)"/>}
                <span style={{ fontWeight: 700, fontSize: 'var(--fs-sm)' }}>
                  {role === 'student' ? 'Student' : 'Parent'} Account
                </span>
                <button type="button" onClick={() => { setRole(''); setError(''); setChildName(''); }}
                  style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>
                  Change
                </button>
              </div>

              {/* Name */}
              <div className="input-group">
                <label htmlFor="login-name">Your Name</label>
                <input id="login-name" type="text" className="input"
                  placeholder={role === 'parent' ? 'Your name' : 'Your full name'}
                  value={name} onChange={e => setName(e.target.value)} required/>
                {name.trim() && mode === 'signup' && (
                  <small style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-xs)', marginTop: 4, display: 'block' }}>
                    Your {role === 'parent' ? 'Parent' : 'Student'} ID will be:{' '}
                    <strong>{role === 'parent' ? `parent_${makeUserId(name)}` : makeUserId(name)}</strong>
                  </small>
                )}
              </div>

              {/* Child's Student ID (parents only) */}
              {role === 'parent' && (
                <div className="input-group">
                  <label htmlFor="child-id">Child&apos;s Student ID</label>
                  <div style={{ position: 'relative' }}>
                    <input id="child-id" type="text" className="input"
                      placeholder="e.g. prashil_kagathara"
                      value={childId}
                      onChange={e => { setChildId(makeUserId(e.target.value)); setChildName(''); }}
                      onBlur={handleChildIdBlur}
                      required
                      style={{ paddingRight: childName ? '2.5rem' : undefined }}/>
                    {childName && (
                      <CheckCircle size={18} color="var(--success)"
                        style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)' }}/>
                    )}
                  </div>
                  {childName
                    ? <small style={{ color: 'var(--success)', fontSize: 'var(--fs-xs)', marginTop: 4, display: 'block', fontWeight: 600 }}>✓ Found: {childName}</small>
                    : <small style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-xs)', marginTop: 4, display: 'block' }}>Ask your child for their Student ID — shown on the Settings page.</small>
                  }
                </div>
              )}

              {/* Password (visual only — no real auth backend) */}
              <div className="input-group">
                <label htmlFor="login-password">Password</label>
                <div style={{ position: 'relative' }}>
                  <input id="login-password" type={showPwd ? 'text' : 'password'} className="input"
                    placeholder="Enter password"
                    value={password} onChange={e => setPassword(e.target.value)}
                    style={{ paddingRight: '3rem' }}/>
                  <button type="button" onClick={() => setShowPwd(p => !p)}
                    style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}
                    aria-label="Toggle password visibility">
                    {showPwd ? <EyeOff size={18}/> : <Eye size={18}/>}
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="error-box" style={{ marginBottom: 'var(--space-md)' }}>{error}</div>
              )}

              {/* Submit */}
              <button type="submit" className="btn btn-primary"
                style={{ width: '100%', marginBottom: 'var(--space-md)' }}
                disabled={submitting}>
                {submitting
                  ? <><Loader2 size={18} style={{ animation: 'spin .8s linear infinite' }}/> Signing in…</>
                  : <>{mode === 'login' ? 'Sign In' : 'Create Account'} <ArrowRight size={18}/></>
                }
              </button>

              {/* Toggle mode */}
              <p style={{ textAlign: 'center', fontSize: 'var(--fs-sm)', color: 'var(--text-muted)', margin: 0 }}>
                {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
                <button type="button" onClick={switchMode}
                  style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontWeight: 700, fontSize: 'var(--fs-sm)' }}>
                  {mode === 'login' ? 'Sign Up' : 'Sign In'}
                </button>
              </p>
            </form>
          )}
        </div>

        {/* Footer hint */}
        <p style={{ textAlign: 'center', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', marginTop: '1.5rem' }}>
          Your Student ID is auto-generated from your name and stored securely.
        </p>
      </div>
    </div>
  );
}
