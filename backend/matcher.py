from sentence_transformers import SentenceTransformer
import numpy as np
from fastapi import HTTPException

def chunk_resume_by_section(text: str)->dict:
    
    
    sections = {}
    section_headers = [
        "education" , "experience", "projects",
        "skills", "achievements", "certifications",
    ]
    text_lower = text.lower()

    #finding position of each section header

    section_positions = {}    
    for header in section_headers:
        pos = text_lower.find(header)
        if pos != -1:
            section_positions[header] = pos
    
    sorted_sections = sorted(section_positions.items(),key=lambda x: x[1])

    #extract text b/w consecutive section positions
    for i, (header,pos) in enumerate(sorted_sections):
        if i+1<len(sorted_sections):
            next_pos = sorted_sections[i+1][1]
            sections[header]=text[pos:next_pos]
        else:
            sections[header] = text[pos:]
    return sections

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text:str):
    return model.encode(text)

def cosine_similarity(vec1,vec2)->float:
    dot_product = np.dot(vec1,vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product/(norm1*norm2)

def match_resume_to_jd(resume_text:str, jd_text:str)->dict:

    #1.chunk resume
    sections = chunk_resume_by_section(resume_text)

    #2 embed each chunk
    section_embeddings={}
    for section_name, section_text in sections.items():
        section_embeddings[section_name]=get_embedding(section_text)

     #3. embed the JD
    jd_embed = get_embedding(jd_text)

    #4 find the most relevant  fxn
    best_section = None
    best_score = 0

    for section_name,embedding in section_embeddings.items():
            score = cosine_similarity(embedding,jd_embed)
            if score>best_score:
                best_score = score
             
                best_section = section_name
    if best_section is None:
        raise HTTPException(
            status_code=400,
            detail="Could not identify resume sections. Please check your resume format."
        )
    
    return {
        "match_score": float(round(best_score * 100, 2)),
        "most_relevant_section": best_section,
        "relevant_text": sections[best_section]
    }
    