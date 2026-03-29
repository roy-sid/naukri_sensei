import language_tool_python
import re
from groq import Groq
from fastapi import HTTPException
import requests
import json

fatal_deduction = 15
quality_deduction = 6

action_verbs = [
    "built", "designed", "developed", "implemented", "created",
    "engineered", "optimized", "automated", "deployed", "integrated",
    "architected", "led", "managed", "improved", "reduced"
]

def check_contact_info(text:str)->bool:
    has_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    has_phone = re.search(r'(\+91[\s-]?)?[6-9]\d{9}', text)
    return bool(has_email and has_phone)

def check_projects_section(text:str)->bool:
    text = text.lower()
    return "project" in text or "projects" in text

def check_education_section(text:str)->bool:
    text = text.lower()
    return "education" in text or "b.tech" in text or "bachelors in technology" in text or "bachelor in technology" in text

def check_grammar(text:str)->bool:
    tool = language_tool_python.LanguageTool('en-US')
    errors = tool.check(text)
    return len(errors) < 5

def get_grammar_errors(text:str)->list:
    tool = language_tool_python.LanguageTool('en-US')
    errors = tool.check(text)
    return [
        {
            "message": error.message,
            "content": error.context,
            "suggestions": error.replacements[:3]
        }
        for error in errors
    ]

def check_action_verbs(text:str)->bool:
    lines = text.split('\n')
    bullet_lines = [line for line in lines if line.startswith(('*', '-', '•'))]

    if not bullet_lines:
        return False
    for line in bullet_lines:
        first_word = line.strip().lstrip('•-* ').lower().split(' ')[0]
        if first_word not in action_verbs:
            return False
    return True

def check_quantification(text:str)->bool:
    lines = text.split('\n')
    bullet_lines = [line for line in lines if line.startswith(('*', '-', '•'))]

    for line in bullet_lines:
        if re.search(r'\d+', line):
            return True
    return False

def check_length(text:str)->bool:
    word_count =  len(text.split())
    return 400<=word_count<=600
       

def check_skills_in_projects(text:str)->bool:
    text_lower = text.lower()

    skills_start = text_lower.find('skills')
    projects_start = text_lower.find('projects')

    if skills_start==-1 or projects_start == -1:
        return False

    skills_text = text_lower[skills_start:projects_start]
    projects_text = text_lower[projects_start:]

    skills = [s.strip() for s in skills_text.split(',')]

    matched = 0
    for skill in skills:
        if skill in projects_text:
            matched +=1
    return matched/len(skills)>0.3

def score_resume(text:str) -> dict:
    score = 100
    feedback = []

    #Fatal Checks
    if not check_contact_info(text):
        score -= 15
        feedback.append("Missing contact info! Please add your email and phone number")

    if not check_projects_section(text):
        score -= 15
        feedback.append("No projects section found — add at least 2-3 relevant projects")

    if not check_education_section(text):
        score -= 15
        feedback.append("No education section found — add your degree and institution")
    
    if not check_skills_in_projects(text):
        score -= 15
        feedback.append("Your listed skills don't appear in your projects! make sure your project descriptions reflect your tech stack")

    if not check_action_verbs(text):
        score-=6
        feedback.append("Your Bullet points are not starting from any action verbs, use action verbs to make your sentences more impactful")

    if not check_quantification(text):
        score -= 6
        feedback.append("You have not added any quantifiable impact please add them")

    if not check_length(text):
        score -= 6
        feedback.append("Your resume exceeds one page limit, Please Limit the resume to 1 page only")

    if not check_grammar(text):
        score -= 6
        feedback.append("Your Resume has many grammar errors. Please Correct them")

    return {"score":score, "feedback":feedback}

RESUME_ANALYSIS_PROMPT = """
You are a senior talent acquisition expert at a top tech company. 
Analyze the resume below and return your analysis in this exact JSON format:

{
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "improvements": ["specific improvement 1", "specific improvement 2"],
    "shortlisting_verdict": "would shortlist / would not shortlist",
    "verdict_reason": "one line reason"
}

Return ONLY the JSON. No preamble, no explanation outside the JSON.
"""

def llm_resume_analysis(text:str)->dict:
    try:
        client = Groq()

        response = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages = [
                {"role": "system", "content": RESUME_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Analyze this resume:\n{text}"}
            ],
            temperature = 0

        )
        raw = response.choices[0].message.content
        clean = raw.replace("```json","").replace("```","").strip()
        return json.loads(clean)
    
    except Exception as e:
        
        raise HTTPException(
            status_code = 503,

            detail="Resume Analysis Service Temporarily Unavailable. Please Try Again After Sometime"
        )
    

    