'use client';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { Loader2 } from 'lucide-react';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({ pdfUrl, onDocumentLoadSuccess, pageNumber, localFontSize }) {
  return (
    <Document
      file={pdfUrl}
      onLoadSuccess={onDocumentLoadSuccess}
      loading={
        <div className="flex-center" style={{ height: 400, color: 'var(--text-muted)' }}>
          <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', marginRight: 8 }}/>
          Loading PDF...
        </div>
      }
    >
      <Page 
        pageNumber={pageNumber} 
        scale={localFontSize} 
        renderTextLayer={true}
        renderAnnotationLayer={true}
      />
    </Document>
  );
}
