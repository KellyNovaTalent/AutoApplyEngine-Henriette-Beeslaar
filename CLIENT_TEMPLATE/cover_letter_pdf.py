"""
Generate PDF cover letters for job applications.
"""
from fpdf import FPDF
import os
from datetime import datetime
import unicodedata

def sanitize_text_for_pdf(text: str) -> str:
    """
    Sanitize Unicode text for FPDF (Latin-1 compatible).
    Replaces common Unicode characters with ASCII equivalents.
    """
    # Replace common Unicode characters
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '--',  # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2026': '...',  # ellipsis
        '\u00a0': ' ',  # non-breaking space
    }
    
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Remove any remaining non-Latin-1 characters
    # Try to decompose accented characters (é -> e)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('latin-1', errors='ignore').decode('latin-1')
    
    return text

def save_cover_letter_as_pdf(cover_letter_text: str, job_title: str, company_name: str) -> str:
    """
    Save cover letter as a PDF file.
    
    Args:
        cover_letter_text: The cover letter text (may contain Unicode)
        job_title: Job title for filename
        company_name: Company name for filename
    
    Returns:
        Path to the saved PDF file
    """
    try:
        # Create cover_letters directory if it doesn't exist
        os.makedirs('cover_letters', exist_ok=True)
        
        # Clean filename
        safe_job = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"cover_letters/CoverLetter_{safe_company}_{safe_job}_{timestamp}.pdf"
        
        # Sanitize text for PDF compatibility
        sanitized_text = sanitize_text_for_pdf(cover_letter_text)
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 11)
        
        # Add cover letter text
        # Split by newlines and handle multi-line text
        for line in sanitized_text.split('\n'):
            if line.strip():
                pdf.multi_cell(0, 6, line)
            else:
                pdf.ln(3)  # Add spacing for blank lines
        
        # Save PDF
        pdf.output(filename)
        
        print(f"   💾 Cover letter saved: {filename}")
        return filename
        
    except Exception as e:
        print(f"   ❌ Failed to create cover letter PDF: {e}")
        print(f"   💡 Tip: Check for special characters in cover letter text")
        raise
