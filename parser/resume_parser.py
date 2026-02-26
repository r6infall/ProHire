import json
import re
from parser.groq_client import ask_groq
from utils.text_cleaner import normalize_text
from utils.college_tier import classify_college_tier

from parser.prompts import RESUME_PARSE_PROMPT

def parse_resume(text: str):
    prompt = RESUME_PARSE_PROMPT.format(resume=text)
    raw = ask_groq(prompt, model="llama-3.3-70b-versatile")

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(cleaned)
    except:
        data = {}

    # ----------- FIX PROJECTS (always consistent) -----------
    final_projects = []
    for p in data.get("projects", []):
        if isinstance(p, dict):
            final_projects.append({
                "title": p.get("title", "").strip() or "Untitled Project",
                "summary": p.get("summary", "").strip() or "No summary provided"
            })
        elif isinstance(p, str):
            final_projects.append({
                "title": p[:40] + "...",
                "summary": p
            })

    data["projects"] = final_projects
    # ---------------------------------------------------------

    # normalize
    data["skills"] = [s.lower().strip() for s in data.get("skills", [])]
    data["college_tier"] = classify_college_tier(data.get("college"))

    # fill missing fields safely
    data.setdefault("name", None)
    data.setdefault("experience_years", 0)
    data.setdefault("cgpa", None)
    data.setdefault("college", None)

    return data
