from groq import Groq
import json
from fastapi import HTTPException

GAP_ANALYSIS_PROMPT = """
You are an experienced talent acquisitor at a top tech company.

Analyze the provided resume section against the job description.
Return ONLY a JSON in this exact format:

{
    "gaps": ["missing skill or keyword 1", "missing skill 2"],
    "improvements": ["specific improvement suggestion 1", "suggestion 2"],
    "suggested_keywords": ["keyword 1", "keyword 2"]
}

Return ONLY the JSON. No preamble, no explanation outside the JSON.
"""

def analyze_gap(relevant_chunk:str, jd_text:str)->dict:
    try:
        client = Groq()
        response = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": GAP_ANALYSIS_PROMPT},
                {"role":"user", "content":f"Resume Section:\n{relevant_chunk}\nJob Description:\n{jd_text}"}

            ],
            temperature=0
        )
        raw = response.choices[0].message.content
        clean = raw.replace("```json","").replace("```","").strip()
        return json.loads(clean)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Gap Analysis Service Temporarily Unavailable. Please Try Again After Sometime"
        )
    

JOB_ROLE_PROMPT = """
Given this resume, suggest the single most suitable job title to search for.
Return only the job title, nothing else.
"""

def extract_job_title(resume_text: str) -> str:
    client = Groq()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": JOB_ROLE_PROMPT},
            {"role": "user", "content": f"Resume:\n{resume_text}"}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()