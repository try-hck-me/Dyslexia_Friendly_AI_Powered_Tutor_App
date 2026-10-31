'use client';
import AppShell from '@/components/layout/AppShell';
import TTSButton from '@/components/tts/TTSButton';
import { useAccessibility } from '@/context/AccessibilityContext';
import { useState, useEffect } from 'react';
import { Search, ZoomIn, ZoomOut, AlignJustify, Type, Maximize2, Minimize2, FileText, Loader2, Trash2, ArrowLeft, ArrowRight } from 'lucide-react';
import { getDocuments, deleteDocument } from '@/lib/api';
import { API_BASE } from '@/lib/constants';
import dynamic from 'next/dynamic';

const PDFViewer = dynamic(() => import('@/components/pdf/PDFViewer'), {
  ssr: false,
  loading: () => <div className="flex-center" style={{ height: 400, color: 'var(--text-muted)' }}><Loader2 size={24} style={{ animation: 'spin 1s linear infinite', marginRight: 8 }}/>Loading PDF engine...</div>
});

export default function ReaderPage() {
  const a11y = useAccessibility();
  const [focusMode, setFocusMode] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [localFontSize, setLocalFontSize] = useState(a11y.fontSize);
  const [localLineHeight, setLocalLineHeight] = useState(a11y.lineHeight);

  // Text selection states
  const [selectionText, setSelectionText] = useState('');
  const [popoverPos, setPopoverPos] = useState(null);

  // Dynamic document states
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState('');
  
  // PDF states
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  // 1. Fetch available documents on mount
  useEffect(() => {
    getDocuments().then(res => {
      if (res.success && res.data?.documents?.length > 0) {
        setDocuments(res.data.documents);
        setSelectedDoc(res.data.documents[0]); // Auto-select first doc
      }
    }).catch(console.error);
  }, []);

  // Reset page when doc changes
  useEffect(() => {
    setPageNumber(1);
    setSelectionText('');
  }, [selectedDoc]);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  const handleSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    if (text) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setSelectionText(text);
    } else {
      setSelectionText('');
    }
  };

  const clearSelection = () => {
    setSelectionText('');
    window.getSelection().removeAllRanges();
  };

  const handleDelete = async () => {
    if (!selectedDoc) return;
    if (!confirm(`Are you sure you want to delete ${selectedDoc}?`)) return;
    
    try {
      await deleteDocument(selectedDoc);
      // Remove from local list
      const updatedDocs = documents.filter(d => d !== selectedDoc);
      setDocuments(updatedDocs);
      if (updatedDocs.length > 0) {
        setSelectedDoc(updatedDocs[0]);
      } else {
        setSelectedDoc('');
      }
      
      // Also attempt to clean up localStorage if it exists so My Documents stays in sync
      try {
        const saved = localStorage.getItem('dyslexia_docs');
        if (saved) {
          const parsed = JSON.parse(saved);
          const filtered = parsed.filter(f => f.name !== selectedDoc);
          localStorage.setItem('dyslexia_docs', JSON.stringify(filtered));
        }
      } catch (e) {}
      
    } catch (err) {
      console.error("Failed to delete document:", err);
      alert("Failed to delete document.");
    }
  };

  const pdfUrl = selectedDoc ? `${API_BASE}/static/${encodeURIComponent(selectedDoc)}` : null;

  return (
    <AppShell>
      {!focusMode && (
        <div className="page-header flex-between">
          <div>
            <h1 className="page-title">PDF Reader 📖</h1>
            <p className="page-subtitle">Read your notes in a comfortable, distraction-free format.</p>
          </div>
          
          {/* Document Selector */}
          {documents.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
              <FileText size={18} color="var(--accent)"/>
              <select 
                className="input" 
                value={selectedDoc} 
                onChange={(e) => setSelectedDoc(e.target.value)}
                style={{ py: '0.4rem', minWidth: 200 }}
              >
                {documents.map(doc => (
                  <option key={doc} value={doc}>{doc}</option>
                ))}
              </select>
              <button 
                className="btn-icon" 
                onClick={handleDelete} 
                title="Delete this document"
                style={{ color: 'var(--error)' }}
              >
                <Trash2 size={18} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className="card" style={{ padding: 'var(--space-sm) var(--space-md)', marginBottom: 'var(--space-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
        <button className="btn-icon" title="Decrease font" onClick={() => setLocalFontSize(p => Math.max(0.875, p - 0.0625))}><ZoomOut size={18}/></button>
        <span style={{ fontSize: 'var(--fs-xs)', minWidth: 50, textAlign: 'center' }}>{localFontSize.toFixed(2)}rem</span>
        <button className="btn-icon" title="Increase font" onClick={() => setLocalFontSize(p => Math.min(1.75, p + 0.0625))}><ZoomIn size={18}/></button>

        <div style={{ width: 1, height: 24, background: 'var(--border)', margin: '0 4px' }}/>

        <button className="btn-icon" title="Adjust spacing" onClick={() => setLocalLineHeight(p => p >= 2.5 ? 1.4 : p + 0.2)}>
          <AlignJustify size={18}/>
        </button>

        <button className="btn-icon" title={`Font: ${a11y.fontFamily === 'normal' ? 'Lexend' : a11y.fontFamily === 'atkinson' ? 'Atkinson Hyperlegible' : 'OpenDyslexic'}`}
          onClick={() => {
            const fonts = ['normal', 'opendyslexic', 'atkinson'];
            const nextIdx = (fonts.indexOf(a11y.fontFamily || 'normal') + 1) % fonts.length;
            a11y.set('fontFamily', fonts[nextIdx]);
          }}
          style={{ color: a11y.fontFamily !== 'normal' ? 'var(--accent)' : 'var(--text-muted)' }}>
          <Type size={18}/>
        </button>

        <button className="btn-icon" title="Search" onClick={() => setShowSearch(!showSearch)}>
          <Search size={18}/>
        </button>

        <button className="btn-icon" title={focusMode ? 'Exit focus' : 'Focus mode'} onClick={() => setFocusMode(!focusMode)}>
          {focusMode ? <Minimize2 size={18}/> : <Maximize2 size={18}/>}
        </button>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
          {numPages && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button className="btn-icon btn-sm" disabled={pageNumber <= 1} onClick={() => setPageNumber(p => p - 1)} title="Previous Page">
                <ArrowLeft size={16}/>
              </button>
              <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 600 }}>Page {pageNumber} of {numPages}</span>
              <button className="btn-icon btn-sm" disabled={pageNumber >= numPages} onClick={() => setPageNumber(p => p + 1)} title="Next Page">
                <ArrowRight size={16}/>
              </button>
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-lg)', alignItems: 'flex-start' }}>
        {/* Main Content: PDF Viewer */}
        <div className="card" style={{
          flex: 1,
          padding: 'var(--space-lg)',
          minHeight: '60vh',
          display: 'flex',
          justifyContent: 'center',
          overflowX: 'auto',
          background: '#f1f5f9',
        }}>
          {pdfUrl ? (
            <div onMouseUp={handleSelection} onKeyUp={handleSelection} style={{ boxShadow: 'var(--shadow-md)', background: 'white' }}>
              <PDFViewer
                pdfUrl={pdfUrl}
                onDocumentLoadSuccess={onDocumentLoadSuccess}
                pageNumber={pageNumber}
                localFontSize={localFontSize}
              />
            </div>
          ) : (
            <div className="flex-center" style={{ height: '100%', flexDirection: 'column', color: 'var(--text-muted)', textAlign: 'center', width: '100%' }}>
              <FileText size={48} style={{ opacity: 0.2, marginBottom: 16 }}/>
              <p>No document selected.</p>
              <p style={{ fontSize: 'var(--fs-sm)' }}>💡 Upload a PDF from the Dashboard to see your study material here.</p>
            </div>
          )}
        </div>

        {/* Sidebar for Selection */}
        {selectionText && (
          <div className="card" style={{ width: 320, flexShrink: 0, padding: 'var(--space-lg)', position: 'sticky', top: 'var(--space-xl)' }}>
            <div className="flex-between" style={{ marginBottom: 'var(--space-md)' }}>
              <h3 style={{ fontSize: 'var(--fs-base)', color: 'var(--accent)', margin: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
                <FileText size={18} /> Selected Text
              </h3>
              <TTSButton text={selectionText} size={16}/>
            </div>
            
            <div style={{
              background: 'var(--bg-alt)',
              padding: 'var(--space-md)',
              borderRadius: 'var(--radius-sm)',
              borderLeft: '4px solid var(--accent)',
              fontFamily: 'var(--font-primary)',
              fontSize: '1.1rem',
              lineHeight: 1.8,
              color: 'var(--text)',
              maxHeight: '50vh',
              overflowY: 'auto'
            }}>
              {selectionText}
            </div>
            
            <button className="btn btn-ghost" style={{ width: '100%', marginTop: 'var(--space-md)' }} onClick={clearSelection}>
              Clear Selection
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
