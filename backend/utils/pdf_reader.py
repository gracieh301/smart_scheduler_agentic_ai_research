from PyPDF2 import PdfReader
import io

def extract_text_from_pdfs(files):
    """Extract text from a list of uploaded PDF files"""
    all_text = ""
    for f in files:
        pdf = PdfReader(io.BytesIO(f))
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    return all_text
