import io
import pypdf
import pdfplumber
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts raw text from a PDF file using pdfplumber, falling back to pypdf."""
    text = ""
    # Try pdfplumber first (typically better at formatting and whitespace)
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}. Trying pypdf...")
        
    # Fallback to pypdf
    if not text.strip():
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text)
        except Exception as e:
            logger.error(f"pypdf failed: {e}")
            
    return text.strip()
