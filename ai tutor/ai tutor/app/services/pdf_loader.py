"""
PDF text extraction using pypdf.
Extracts text page-by-page from uploaded PDF files.
"""

from io import BytesIO
from pypdf import PdfReader
from app.utils.formatter import clean_text


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF file given as bytes.
    
    Args:
        file_bytes: Raw bytes of the PDF file.
        
    Returns:
        Cleaned, concatenated text from all pages.
    """
    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages_text.append(text.strip())

    full_text = "\n\n".join(pages_text)
    return clean_text(full_text)


def extract_text_with_metadata(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extract text page-by-page with metadata.
    
    Returns:
        List of dicts with 'text', 'page', 'source' keys.
    """
    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    pages = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({
                "text": clean_text(text.strip()),
                "page": page_num + 1,
                "source": filename,
            })

    return pages
