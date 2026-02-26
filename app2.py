import streamlit as st
import pdfplumber
import fitz
import re
import streamlit as st
import pdfplumber
import fitz  
import re
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --------------------------------------------
# PDF Extractors
# --------------------------------------------
def extract_text_pdfplumber(file_bytes):
    text = []
    with pdfplumber.open(file_bytes) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def extract_text_pymupdf(file_bytes):
    file_bytes.seek(0)
    text = []
    doc = fitz.open(stream=file_bytes.read(), filetype="pdf")
    for page in doc:
        text.append(page.get_text("text"))
    return "\n".join(text)

# Simple normalizer
def normalize_text(s):
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()

SKILL_EXP_COLLEGE_PROMPT = """
Extract ONLY the following information from the resume text:

Return output as STRICT JSON only:
{{
  "skills": ["python", "machine learning", ...],
  "experience_years": <number>, 
  "college": "<college name>"
  "cgpa": <8.5>
}}

Rules:
- "skills": Only technical skills (programming languages, frameworks, tools, ML/AI, cloud, databases). 1–3 words each.
- "experience_years": Extract total professional experience. If not found, return 0.
- "college": Extract highest education institute name ONLY (no course, no year).
- "cgpa": extract CGPA / GPA / Grade (out of 10 or 4). If not found, return null.

STRICT RULES:
- Return ONLY valid JSON.
- No explanation, no comments, no markdown.
- If something is missing, return it as null or [].
  
Resume:
---
{resume}
---
"""

def classify_college_tier(college_name):
    if not college_name:
        return None

    col = college_name.lower()

    tier1_keywords = [
        "iit", "indian institute of technology",
        "nit", "national institute of technology",
        "iiit", "indian institute of information technology",
        "bits", "birla institute",
        "vit vellore", "vellore institute of technology",
        "dtu", "delhi technological university",
        "nsut", "nsit", "netaji subhas",
        "coep", "college of engineering pune",
        "manipal", "mit manipal",
        "ict mumbai", "institute of chemical technology"
    ]

    tier2_keywords = [
        "government engineering college",
        "state institute",
        "state engineering",
        "sppu", "rtmnu",
        "srm", "amity", "chandigarh university",
        "pes university", "rv college",
        "vit bhopal", "vit chennai"
    ]

    if any(k in col for k in tier1_keywords):
        return "Tier 1"
    elif any(k in col for k in tier2_keywords):
        return "Tier 2"
    else:
        return "Tier 3"


def skill_exp_college_extractor(resume_text):
    prompt = SKILL_EXP_COLLEGE_PROMPT.format(resume=resume_text)

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        out = response.text.strip()

        # remove optional json fences if present
        out = re.sub(r"^```json|```$", "", out).strip()

        data = json.loads(out)

        # normalize skills
        skills = [s.lower().strip() for s in data.get("skills", [])]

        college = data.get("college", None)
        college_tier = classify_college_tier(college)
        cgpa = data.get("cgpa", None)
        return {
            "skills": skills,
            "experience_years": data.get("experience_years", 0),
            "college": college,
            "college_tier": college_tier,
            "cgpa": cgpa
        }

    except Exception as e:
        print("LLM error:", e)
        return {
            "skills": [],
            "experience_years": 0,
            "college": None,
            "college_tier": None,
            "cgpa": None
        }

def parse_jd(jd_text):
    if "," in jd_text:
        # comma separated skills
        return [s.strip().lower() for s in jd_text.split(",") if s.strip()]
    else:
        # full paragraph: send raw to LLM later
        return jd_text.strip()
user_prompt = """
Hey Gemini, you have a task.

I am providing you:
1. The candidate's extracted resume skills
2. The job description requirements

Your job:
Compare the resume skills with the job description and return a JSON object with this EXACT structure:

{{
  "mapped": [],
  "substitutes": [],
  "extras": [],
  "score": 0,
  "review": ""
}}

### Behaviour Rules:

1. **mapped**  
   - Direct matches between candidate skills and JD skills.

2. **substitutes**  
   - Cases where candidate doesn't have the exact JD skill,  
     but has a related/alternative skill that implies competence.  
   - Example: JD asks for “machine learning engineer” but resume shows “tensorflow”,  
     or JD says “cloud experience” but resume says “aws”.

3. **extras**  
   - Skills the candidate has that are NOT required by JD.

4. **score (1–100)**  
   - How well the candidate fits the job **based on your comparison**.

5. **review**  
   - A short 1–2 line professional summary of the candidate’s fit.

Return ONLY the JSON. No explanation outside JSON.

Here is the data:

Resume Skills:
{resume_skills}

Job Description:
{jd_text}
"""

def call_llm_for_matching(resume_skills, jd_input, user_prompt):
    """
    Sends resume skills + JD + your custom prompt to Gemini.
    """
    final_prompt = user_prompt.format(
        resume_skills=json.dumps(resume_skills, indent=2),
        jd_text=jd_input
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(final_prompt)
        text = response.text.strip()
        text = re.sub(r"^```(json)?", "", text)
        text = re.sub(r"```$", "", text)
        return text
    except Exception as e:
        return f"LLM Error: {str(e)}"

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------
st.set_page_config(page_title="HirePro – Resume Text Extractor", layout="wide")
st.title("🔥 HirePro – PDF Resume Text Extractor (Only Parsing)")

uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

# -- SESSION STATE INIT --
if "skills" not in st.session_state:
    st.session_state.skills = []

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

import html
# ------------------------------------------------------------
# BUTTON 1: Extract Resume + Skills
# ------------------------------------------------------------
if st.button("Extract Resume Text"):
    if not uploaded:
        st.error("Please upload a resume.")
        st.stop()

    uploaded.seek(0)
    text1 = extract_text_pdfplumber(uploaded)

    uploaded.seek(0)
    text2 = extract_text_pymupdf(uploaded)

    resume_text = normalize_text(text1 + "\n" + text2)

    st.session_state.resume_text = resume_text
    st.session_state.extracted = skill_exp_college_extractor(resume_text)

    st.success("Resume processed successfully!")


# --- SHOW RESULT CARDS ---
if "extracted" in st.session_state and st.session_state.extracted:

    data = st.session_state.extracted
    skills = data.get("skills", [])
    exp = data.get("experience_years", 0)
    college = data.get("college", "Not Found")
    tier = data.get("college_tier", "Not Determined")
    cgpa = data.get("cgpa", None)
    
    st.subheader("📄 Extracted Resume Insights")

    # --- CARD CONTAINER ---
    st.markdown(
        """
        <style>
            .card {
                padding: 20px;
                border-radius: 12px;
                background: #111827;
                border: 1px solid #1F2937;
                color: white;
                margin-bottom: 20px;
            }
            .pill-container { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 8px;
                margin-top: 10px;
            }
            .pill {
                background: #2563EB;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 13px;
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- SKILLS CARD ---
    skills_html = "".join([f"<span class='pill'>{html.escape(s)}</span>" for s in skills])

    st.markdown(
        f"""
        <div class='card'>
            <h3>🧠 Technical Skills</h3>
            <div class='pill-container'>{skills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- EXPERIENCE CARD ---
    st.markdown(
        f"""
        <div class='card'>
            <h3>💼 Experience</h3>
            <p style='font-size:18px;'>{exp} years</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- EDUCATION CARD ---
    st.markdown(
        f"""
        <div class='card'>
            <h3>🎓 Education</h3>
            <p><strong>College:</strong> {college}</p>
            <p><strong>Tier:</strong> {tier}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- CGPA CARD ---
    st.markdown(
        f"""
        <div class='card'>
            <h3>🎯 CGPA</h3>
            <p style='font-size:18px;'>
                {cgpa if cgpa not in [None, ""] else "Not Available"}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# JD INPUT FIELD (always visible)
# ------------------------------------------------------------
st.session_state.jd_text = st.text_area(
    "Paste Job Description (comma-separated OR full JD)",
    value=st.session_state.jd_text
)


# ------------------------------------------------------------
# BUTTON 2: ANALYZE WITH LLM
# ------------------------------------------------------------
if st.button("Analyze with LLM"):

    skills = st.session_state.skills
    jd_text = st.session_state.jd_text

    if not skills:
        st.error("Please extract resume text first.")
        st.stop()

    if jd_text.strip() == "":
        st.error("Please paste the Job Description.")
        st.stop()

    jd_input = parse_jd(jd_text)

    # Convert JD input safely to string
    if isinstance(jd_input, list):
        jd_input_formatted = json.dumps(jd_input, indent=2)
    else:
        jd_input_formatted = jd_input

    llm_output = call_llm_for_matching(
        resume_skills=skills,
        jd_input=jd_input_formatted,
        user_prompt=user_prompt
    )

    # st.subheader("🤖 LLM Raw Response (debug)")
    # st.code(llm_output)

    # Try JSON
    try:
        parsed = json.loads(llm_output)
        st.subheader("✨ Final Parsed Output")
        # st.json(parsed)

        st.markdown("### ✔ Mapped Skills")
        st.write(parsed.get("mapped", []))

        st.markdown("### 🔄 Substitutes")
        st.write(parsed.get("substitutes", []))

        st.markdown("### ➕ Extras")
        st.write(parsed.get("extras", []))

        st.markdown("### ⭐ Score")
        st.metric("Candidate Score", f"{parsed.get('score', 0)}/100")

        st.markdown("### 📝 Review")
        st.write(parsed.get("review", ""))

    except:
        st.error("LLM did not return valid JSON.")
        st.code(llm_output)



# for activating venv : HirePro\Scripts\activate
# for running application : streamlit run app2.py
