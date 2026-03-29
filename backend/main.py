from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from resume_parser import extract_text
from scorer import score_resume, llm_resume_analysis, get_grammar_errors
from matcher import match_resume_to_jd
from analyzer import analyze_gap, extract_job_title
import httpx
import os


from dotenv import load_dotenv
load_dotenv()



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    try:
        text = await extract_text(file)
        score_data = score_resume(text)
        llm_data = llm_resume_analysis(text)
        grammar_data = get_grammar_errors(text)

        return {
            "resume_text": text,
            "score": score_data["score"],
            "feedback":score_data["feedback"],
            "llm_analysis":llm_data,
            "grammar_errors":grammar_data,
            


        }
        

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match-resume")
async def match_resume(
        jd_text: str = Form(...),
        file: UploadFile = File(None),
        resume_text: str = Form(None)
):
    try:
          
            if not resume_text:
                text = await extract_text(file)
            else:
                text = resume_text
            score_data = score_resume(text)
            llm_data = llm_resume_analysis(text)
            grammar_data = get_grammar_errors(text)
            
            

            matcher = match_resume_to_jd(text,jd_text)
            gap_analysis= analyze_gap (matcher["relevant_text"], jd_text)

            return{
                "resume_text": text,
                "score": score_data["score"],
                "feedback":score_data["feedback"],
                "llm_analysis":llm_data,
                "grammar_errors":grammar_data,
                "resume_match": matcher,
                "gap_in_resume": gap_analysis
            }
    except Exception as e:
         
         raise HTTPException(status_code=500, detail=str(e))

async def search_jobs(query: str) -> list:
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": query, "num_results": "5"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        data = response.json()
    return data["data"]

@app.post("/search-jobs")
async def search_jobs_endpoint(resume_text: str = Form(...)):
     try:
          job_title = extract_job_title(resume_text)
          jobs = await search_jobs(job_title)
          return{
               "detected_role": job_title,
                "jobs": jobs
            }
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))