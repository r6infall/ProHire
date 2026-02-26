import json
import re
from parser.groq_client import ask_groq

from parser.prompts import JD_PARSE_PROMPT


def parse_jd(text):
    prompt = JD_PARSE_PROMPT.format(jd=text)
    raw = ask_groq(prompt)

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(cleaned)
    except:
        data = {
            "title": "",
            "required_skills": [],
            "nice_to_have_skills": [],
            "min_experience_years": 0,
            "max_experience_years": 10
        }

    data["required_skills"] = [s.lower() for s in data.get("required_skills", [])]
    data["nice_to_have_skills"] = [s.lower() for s in data.get("nice_to_have_skills", [])]

    return data
