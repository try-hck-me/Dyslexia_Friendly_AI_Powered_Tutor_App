'use client';
import AppShell from '@/components/layout/AppShell';
import { useUser } from '@/context/UserContext';
import { useState } from 'react';
import { generateQuiz, submitQuiz } from '@/lib/api';
import { Brain, Loader2, CheckCircle2, XCircle, RotateCcw, ArrowRight, ArrowLeft } from 'lucide-react';
import { DIFFICULTY_COLORS } from '@/lib/constants';

export default function QuizPage() {
  const { effectiveUserId } = useUser();
  const [topic, setTopic]         = useState('');
  const [numQ, setNumQ]           = useState(5);
  const [quiz, setQuiz]           = useState(null);
  const [difficulty, setDifficulty] = useState('medium');
  const [currentQ, setCurrentQ]   = useState(0);
  const [answers, setAnswers]     = useState({});
  const [results, setResults]     = useState(null);
  const [loading, setLoading]     = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]         = useState('');

  const generate = async () => {
    if (!topic.trim()) return;
    setError(''); setQuiz(null); setResults(null); setAnswers({}); setCurrentQ(0);
    setLoading(true);
    try {
      const res = await generateQuiz(effectiveUserId, topic.trim(), numQ);
      if (res.success && res.data?.questions?.length > 0) {
        setQuiz(res.data.questions);
        setDifficulty(res.data.difficulty || 'medium');
      } else {
        setError(res.data?.error || res.error || 'No questions generated. Try a different topic.');
      }
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  const selectAnswer = (qIdx, option) => {
    setAnswers(prev => ({ ...prev, [qIdx]: option }));
  };

  const submit = async () => {
    setSubmitting(true);
    try {
      const ansArray = quiz.map((_, i) => ({ question_index: i, selected: answers[i] || '' }));
      // Pass difficulty back so the backend records the actual level used
      const res = await submitQuiz(effectiveUserId, topic, difficulty, quiz, ansArray);
      if (res.success) setResults(res.data);
      else setError(res.error || 'Submission failed.');
    } catch (err) { setError(err.message); }
    setSubmitting(false);
  };

  const reset = () => { setQuiz(null); setResults(null); setAnswers({}); setCurrentQ(0); setError(''); };
  const dc = DIFFICULTY_COLORS[difficulty] || DIFFICULTY_COLORS.medium;

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">Quiz Generator 🧠</h1>
        <p className="page-subtitle">Test your knowledge with AI-generated quizzes from your notes.</p>
      </div>

      {/* Generate Form */}
      {!quiz && !results && (
        <div className="card" style={{ padding: 'var(--space-xl)', maxWidth: 500 }}>
          <div className="input-group">
            <label htmlFor="topic">What topic do you want to quiz on?</label>
            <input id="topic" className="input" value={topic} onChange={e => setTopic(e.target.value)}
              placeholder="e.g. cells, photosynthesis, acids..." onKeyDown={e => e.key === 'Enter' && generate()}/>
          </div>
          <div className="input-group">
            <label htmlFor="numq">Number of questions</label>
            <select id="numq" className="select" value={numQ} onChange={e => setNumQ(+e.target.value)}>
              {[3,5,7,10].map(n => <option key={n} value={n}>{n} questions</option>)}
            </select>
          </div>
          {error && <div className="error-box" style={{ marginBottom: 'var(--space-md)' }}>{error}</div>}
          <button className="btn btn-primary" onClick={generate} disabled={loading || !topic.trim()} style={{ width: '100%' }}>
            {loading ? <><Loader2 size={18} style={{ animation: 'spin .8s linear infinite' }}/> Generating...</> : <><Brain size={18}/> Generate Quiz</>}
          </button>
        </div>
      )}

      {/* Quiz Questions */}
      {quiz && !results && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-lg)' }}>
            <div>
              <span className="badge" style={{ background: dc.bg, color: dc.text }}>{difficulty}</span>
              <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
                Question {currentQ + 1} of {quiz.length}
              </span>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={reset}>Cancel</button>
          </div>

          {/* Progress */}
          <div className="progress-track" style={{ marginBottom: 'var(--space-lg)' }}>
            <div className="progress-fill" style={{ width: `${((currentQ + 1) / quiz.length) * 100}%` }}/>
          </div>

          {/* Question Card */}
          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <p style={{ fontWeight: 700, fontSize: 'var(--fs-lg)', marginBottom: 'var(--space-lg)' }}>
              {quiz[currentQ].question}
            </p>
            <div className="flex-col" style={{ gap: 'var(--space-sm)' }}>
              {quiz[currentQ].options.map((opt, oi) => (
                <button key={oi} className={`quiz-option ${answers[currentQ] === opt ? 'selected' : ''}`}
                  onClick={() => selectAnswer(currentQ, opt)}>
                  <span style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--fs-sm)', fontWeight: 700, flexShrink: 0, background: answers[currentQ] === opt ? 'var(--accent)' : 'transparent', color: answers[currentQ] === opt ? '#fff' : 'var(--text-muted)' }}>
                    {String.fromCharCode(65 + oi)}
                  </span>
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-lg)' }}>
            <button className="btn btn-ghost" onClick={() => setCurrentQ(p => p - 1)} disabled={currentQ === 0}>
              <ArrowLeft size={16}/> Previous
            </button>
            {currentQ < quiz.length - 1 ? (
              <button className="btn btn-primary" onClick={() => setCurrentQ(p => p + 1)}>
                Next <ArrowRight size={16}/>
              </button>
            ) : (
              <button className="btn btn-primary" onClick={submit} disabled={submitting || Object.keys(answers).length < quiz.length}>
                {submitting ? <><Loader2 size={16} style={{ animation: 'spin .8s linear infinite' }}/> Submitting...</> : 'Submit Quiz'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div>
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-2xl)', marginBottom: 'var(--space-xl)' }}>
            <div style={{ fontSize: '4rem', fontWeight: 800, background: `linear-gradient(135deg, ${results.percentage >= 60 ? 'var(--success)' : 'var(--accent2)'}, var(--accent))`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              {results.score}/{results.total}
            </div>
            <div style={{ fontSize: 'var(--fs-lg)', color: 'var(--text-secondary)', marginTop: 'var(--space-xs)' }}>
              {results.percentage}% — {results.percentage >= 80 ? 'Excellent! 🌟' : results.percentage >= 60 ? 'Good job! 👍' : 'Keep practicing! 💪'}
            </div>
          </div>

          <h3 style={{ marginBottom: 'var(--space-md)' }}>Question Breakdown</h3>
          <div className="flex-col">
            {results.results.map((r, i) => (
              <div key={i} className="card" style={{ padding: 'var(--space-lg)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
                  {r.is_correct ? <CheckCircle2 size={20} color="var(--success)"/> : <XCircle size={20} color="var(--error)"/>}
                  <span style={{ fontWeight: 600 }}>{r.question}</span>
                </div>
                {!r.is_correct && (
                  <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginLeft: 28 }}>
                    <div>Your answer: <span style={{ color: 'var(--error)' }}>{r.selected || '(none)'}</span></div>
                    <div>Correct answer: <span style={{ color: 'var(--success)', fontWeight: 600 }}>{r.correct}</span></div>
                  </div>
                )}
                {r.explanation && <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-muted)', marginLeft: 28, marginTop: 4 }}>💡 {r.explanation}</div>}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-md)', marginTop: 'var(--space-xl)' }}>
            <button className="btn btn-secondary" onClick={reset}><RotateCcw size={16}/> New Quiz</button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
