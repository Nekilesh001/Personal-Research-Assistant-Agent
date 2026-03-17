"""
PDF Extractor using PyMuPDF (fitz).
Extracts text and metadata from user-uploaded PDF files safely.
"""

import fitz
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF byte stream.
    Detects if the PDF is scanned (image-only) and returns an error message.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        
        # Scanned PDF check
        if len(text.strip()) < 50 and doc.page_count > 0:
            return "ERROR: Scanned PDF or no readable text found. OCR is not supported."
            
        return text.strip()
    except Exception as exc:
        logger.error("pdf_text_extraction_failed", error=str(exc))
        return f"ERROR: Failed to extract text from PDF: {str(exc)}"

def extract_metadata(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract document metadata (title, author, year) and page count
    from a PDF byte stream.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        metadata = doc.metadata
        page_count = doc.page_count
        doc.close()
        
        # safely extract year from standard PDF date format (D:YYYYMMDD...)
        creation_date = metadata.get("creationDate", "")
        year = "N/A"
        if creation_date and len(creation_date) > 5 and creation_date.startswith("D:"):
            year = creation_date[2:6]
            
        return {
            "title": metadata.get("title") or "Unknown Title",
            "authors": [metadata.get("author")] if metadata.get("author") else ["Unknown Author"],
            "year": year,
            "page_count": page_count
        }
    except Exception as exc:
        logger.error("pdf_metadata_extraction_failed", error=str(exc))
        return {
            "title": "Unknown Title",
            "authors": ["Unknown Author"], 
            "year": "N/A",
            "page_count": 0
        }
