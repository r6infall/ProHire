import pdfplumber
import fitz

def extract_text_pdfplumber(file):
    text = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)

def extract_text_pymupdf(file):
    file.seek(0)
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([p.get_text("text") for p in doc])
