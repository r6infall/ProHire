# parser/prompts.py

# Resume Parsing Prompt
RESUME_PARSE_PROMPT = """
Extract ALL of the following information from the resume text.

Return STRICT JSON only:

{{
  "name": "",
  "skills": [],
  "experience_years": 0,
  "projects": [
    {{
      "title": "",
      "summary": ""
    }}
  ],
  "cgpa": null,
  "college": ""
}}

RULES:
- "name": Extract the candidate’s full name EXACTLY as written at the top of the resume.
- "skills": Extract all technical skills ONLY (languages, frameworks, tools, databases, CS concepts).
- "experience_years": If no internships or jobs are listed, return 0.
- "projects": Extract ALL real projects mentioned in the resume.
    - Each project must have:
        - "title": exact project name from resume
        - "summary": a short 1–2 line summary
    - Maximum 5 projects.
    - If a project is only mentioned briefly, still extract it.
- "cgpa": Extract the CGPA (e.g., 7.99). If not found return null.
- "college": Extract highest education institute name ONLY (no degree, no batch).

VERY IMPORTANT:
- DO NOT hallucinate.
- DO NOT change project titles.
- If a field is missing, return a valid empty field instead of guessing.

Resume:
---
{resume}
---
"""



# JD Parsing Prompt
JD_PARSE_PROMPT = """
Extract the following information from the job description.

Return STRICT JSON only:

{{
  "title": "",
  "required_skills": [],
  "nice_to_have_skills": [],
  "min_experience_years": 0,
  "max_experience_years": 10
}}

Rules:
- required_skills: All mandatory technical skills.
- nice_to_have_skills: Optional or “preferred” skills.
- If experience range is unclear, return 0 and 10.
- Do NOT hallucinate.

Job Description:
---
{jd}
---
"""



# Reranking Prompt
RERANK_PROMPT = """
You are a recruitment ranking assistant.
Reorder candidate IDs by best job fit.

Return STRICT JSON only:

{{
  "ordered_ids": []
}}

Job Description:
{jd}

Candidates:
{candidates}
"""
