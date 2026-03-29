import pdfplumber
import io
from docx import Document
from fastapi import UploadFile, HTTPException 
#NOTE: HTTPException is used for returning error responses with proper HTTP status codes

async def extract_text(file: UploadFile) -> str:
    contents = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            text = ""
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    extracted = extracted.replace('(cid:135)','\n•')
                    text += extracted

    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(contents))
        text = ""
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
    
    else:
        raise HTTPException(
            status_code = 400,
            detail = "Unsupported file type. Please Upload a PDF or DOCX file."
        )
    
    return text

    