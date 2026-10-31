'use client';
import AppShell from '@/components/layout/AppShell';
import { useState, useRef, useEffect } from 'react';
import { uploadPDF, getUploadStatus, deleteDocument } from '@/lib/api';
import Link from 'next/link';
import {
  Upload, FileText, CheckCircle2, AlertCircle,
  Loader2, Trash2, MessageCircle, Brain, BookOpen,
  Cloud, ArrowRight
} from 'lucide-react';

export default function DocumentsPage() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [justUploaded, setJustUploaded] = useState(false);
  const inputRef = useRef(null);

  // Load from localStorage — only on client
  useEffect(() => {
    const saved = localStorage.getItem('dyslexia_docs');
    if (saved) {
      try { setFiles(JSON.parse(saved)); } catch {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('dyslexia_docs', JSON.stringify(files));
  }, [files]);

  const handleUpload = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) { setError('Only PDF files are supported.'); return; }
    if (file.size > 20 * 1024 * 1024) { setError('File too large. Max 20MB.'); return; }

    setError('');
    setJustUploaded(false);
    setUploading(true);
    setProgress({ percent: 0, status: 'Uploading file…' });

    try {
      const res = await uploadPDF(file);
      if (!res.success) { setError(res.error || 'Upload failed.'); setUploading(false); setProgress(null); return; }

      const filename = res.data?.filename || file.name;
      setProgress({ percent: 10, status: 'Processing PDF…' });

      const poll = setInterval(async () => {
        try {
          const status = await getUploadStatus(filename);
          if (status.success && status.data) {
            setProgress({ percent: status.data.progress || 0, status: status.data.status || 'Processing…' });
            if (status.data.completed || status.data.progress >= 100) {
              clearInterval(poll);
              setUploading(false);
              if (!status.data.error) {
                setFiles(prev => {
                  // Avoid duplicates
                  if (prev.find(f => f.name === filename)) return prev;
                  return [...prev, { name: filename, uploadedAt: new Date().toISOString(), status: 'ready' }];
                });
                setJustUploaded(true);
                setProgress({ percent: 100, status: 'Complete! ✅' });
                setTimeout(() => setProgress(null), 4000);
              } else {
                setError(status.data.error);
                setProgress(null);
              }
            }
          }
        } catch { clearInterval(poll); setUploading(false); setProgress(null); }
      }, 2000);

    } catch (err) {
      setError(err.message);
      setUploading(false);
      setProgress(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  };

  const removeFile = async (idx) => {
    const file = files[idx];
    try {
      await deleteDocument(file.name);
    } catch (err) {
      console.error("Failed to delete from backend:", err);
    }
    setFiles(prev => prev.filter((_, i) => i !== idx));
    setJustUploaded(false);
  };

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">My Documents 📄</h1>
        <p className="page-subtitle">Upload study PDFs — AI will process, chunk and index them automatically.</p>
      </div>

      {/* ── Drop Zone ── */}
      <div
        className={`dropzone ${dragOver ? 'active' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        style={{ marginBottom: 'var(--space-md)' }}>
        <input ref={inputRef} type="file" accept=".pdf" style={{ display: 'none' }}
          onChange={e => handleUpload(e.target.files[0])} disabled={uploading}/>
        <div className="dropzone-icon">
          {uploading
            ? <Loader2 size={48} style={{ animation: 'spin .8s linear infinite' }} color="var(--accent)"/>
            : <Cloud size={48}/>
          }
        </div>
        <p style={{ fontWeight: 700, fontSize: 'var(--fs-lg)', marginBottom: '0.25rem' }}>
          {uploading ? 'Processing your PDF…' : 'Drop your PDF here'}
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', margin: 0 }}>
          {uploading ? 'Please wait while we index your content' : 'or click to browse — PDF only · Max 20MB'}
        </p>
      </div>

      {/* ── Upload Progress Bar ── */}
      {progress && (
        <div className="card" style={{ marginBottom: 'var(--space-lg)', padding: 'var(--space-md) var(--space-lg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 'var(--fs-sm)' }}>
            <span style={{ fontWeight: 600 }}>{progress.status}</span>
            <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{Math.round(progress.percent)}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress.percent}%` }}/>
          </div>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="error-box" style={{ marginBottom: 'var(--space-lg)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={16} style={{ flexShrink: 0 }}/> {error}
        </div>
      )}

      {/* ── Post-Upload Quick Actions ── */}
      {justUploaded && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(76,175,130,0.08), rgba(124,92,252,0.06))',
          border: '1px solid rgba(76,175,130,0.25)',
          borderRadius: 'var(--radius-lg)', padding: 'var(--space-lg)',
          marginBottom: 'var(--space-xl)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-md)' }}>
            <CheckCircle2 size={20} color="var(--success)"/>
            <span style={{ fontWeight: 700, color: 'var(--success)' }}>PDF processed successfully! What would you like to do next?</span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
            {[
              { href: '/chat',   icon: MessageCircle, label: 'Ask Questions', color: '#7C5CFC' },
              { href: '/quiz',   icon: Brain,         label: 'Take a Quiz',   color: '#F5A623' },
              { href: '/reader', icon: BookOpen,      label: 'Read PDF',      color: '#4CAF82' },
            ].map(({ href, icon: Icon, label, color }) => (
              <Link key={href} href={href} className="btn btn-secondary btn-sm"
                style={{ borderColor: color, color }}>
                <Icon size={15}/> {label} <ArrowRight size={13}/>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── File Library ── */}
      {files.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-md)' }}>
            <h3 style={{ margin: 0 }}>Uploaded Documents ({files.length})</h3>
            <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>All are indexed and ready for AI</span>
          </div>
          <div className="flex-col">
            {files.map((f, i) => (
              <div key={i} className="card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-md) var(--space-lg)' }}>
                <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: 'rgba(124,92,252,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FileText size={22} color="var(--accent)"/>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                    Uploaded {new Date(f.uploadedAt).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                  </div>
                </div>
                <span className="badge" style={{ background: 'rgba(76,175,130,0.1)', color: 'var(--success)', flexShrink: 0 }}>
                  <CheckCircle2 size={12}/> Ready
                </span>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <Link href="/chat" title="Ask questions about this doc" className="btn-icon" style={{ color: 'var(--accent)' }}>
                    <MessageCircle size={16}/>
                  </Link>
                  <Link href="/quiz" title="Generate a quiz from this doc" className="btn-icon" style={{ color: 'var(--warning)' }}>
                    <Brain size={16}/>
                  </Link>
                  <button className="btn-icon" onClick={() => removeFile(i)} title="Remove document" aria-label="Remove document"
                    style={{ color: 'var(--error)' }}>
                    <Trash2 size={16}/>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {files.length === 0 && !uploading && (
        <div className="empty-state" style={{ marginTop: 'var(--space-2xl)' }}>
          <div className="empty-icon">📚</div>
          <p className="empty-text">No documents uploaded yet. Drop a PDF above to start your AI-powered study session!</p>
        </div>
      )}
    </AppShell>
  );
}
