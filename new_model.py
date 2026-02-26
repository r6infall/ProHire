import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
import re
import json
import ollama
import uuid

# -------------------------------------------------
# HELPERS: PDF → TEXT, NORMALIZATION
# -------------------------------------------------

def extract_text_pdfplumber(file_obj):
    text = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def extract_text_pymupdf(file_obj):
    file_obj.seek(0)
    text = []
    doc = fitz.open(stream=file_obj.read(), filetype="pdf")
    for page in doc:
        text.append(page.get_text("text"))
    return "\n".join(text)

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# -------------------------------------------------
# COLLEGE TIER MAPPING
# -------------------------------------------------

def classify_college_tier(college_name):
    if not college_name:
        return None
    col = college_name.lower()

    tier1 = [
        "iit", "indian institute of technology",
        "bits", "birla institute",
        "iiit", "indian institute of information technology",
        "nit ", "national institute of technology",
        "vit vellore", "vellore institute of technology",
        "coep", "dtu", "nsut", "manipal", "mit manipal"
    ]

    tier2 = [
        "sppu", "pict", "rtmnu", "amity", "srm",
        "pes", "rv college", "chandigarh university",
        "vit bhopal", "vit chennai"
    ]

    if any(k in col for k in tier1):
        return "Tier 1"
    if any(k in col for k in tier2):
        return "Tier 2"
    return "Tier 3"

# -------------------------------------------------
# OLLAMA CALLS
# -------------------------------------------------

def call_qwen(prompt: str, model="qwen3:4b"):
    """Use Qwen3:4b for parsing resumes + JD."""
    res = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return res["message"]["content"]

def call_gemma(prompt: str, model="gemma3:1b"):
    """Use Gemma3:1b for reranking."""
    res = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return res["message"]["content"]

# -------------------------------------------------
# PROMPTS
# -------------------------------------------------

RESUME_PARSE_PROMPT = """
Extract structured data from the resume text strictly as JSON:

{{
  "name": "Candidate Name",
  "skills": ["python", "react", "..."],
  "experience_years": 2.5,
  "projects": [
    {{"title": "Project title", "summary": "one line"}},
    {{"title": "Project title", "summary": "one line"}}
  ],
  "cgpa": 8.5,
  "college": "College name only"
}}

Rules:
- skills: only technical skills.
- experience_years: numeric.
- cgpa: numeric or null.
- college: no degree, no batch year.
Return STRICT JSON only.

Resume:
---
{resume}
---
"""

JD_PARSE_PROMPT = """
Extract structured data from the job description strictly as JSON:

{{
  "title": "Role title",
  "required_skills": ["python", "aws", "..."],
  "nice_to_have_skills": ["docker", "ml"],
  "min_experience_years": 0,
  "max_experience_years": 3
}}

JD:
---
{jd}
---
"""

RERANK_PROMPT = """
Rank candidates based on the job description and their details.

Return STRICT JSON:

{{
  "ordered_ids": ["id1", "id2", "id3"]
}}

JOB DESCRIPTION:
{jd}

CANDIDATES:
{candidates}
"""

# -------------------------------------------------
# PARSERS USING QWEN
# -------------------------------------------------

def parse_resume(text):
    prompt = RESUME_PARSE_PROMPT.format(resume=text)
    raw = call_qwen(prompt)

    raw_clean = re.sub(r"```json|```", "", raw).strip()
    try:
        data = json.loads(raw_clean)
    except:
        data = {
            "name": None,
            "skills": [],
            "experience_years": 0,
            "projects": [],
            "cgpa": None,
            "college": None,
        }

    return {
        "name": data.get("name"),
        "skills": [s.lower().strip() for s in data.get("skills", [])],
        "experience_years": float(data.get("experience_years", 0)),
        "projects": data.get("projects", []),
        "cgpa": data.get("cgpa"),
        "college": data.get("college"),
        "college_tier": classify_college_tier(data.get("college")),
    }


def parse_jd(jd_text):
    prompt = JD_PARSE_PROMPT.format(jd=jd_text)
    raw = call_qwen(prompt)

    raw_clean = re.sub(r"```json|```", "", raw).strip()
    try:
        data = json.loads(raw_clean)
    except:
        data = {
            "title": None,
            "required_skills": [],
            "nice_to_have_skills": [],
            "min_experience_years": 0,
            "max_experience_years": 10,
        }

    return {
        "title": data["title"],
        "required_skills": [s.lower() for s in data["required_skills"]],
        "nice_to_have_skills": [s.lower() for s in data["nice_to_have_skills"]],
        "min_experience_years": float(data["min_experience_years"]),
        "max_experience_years": float(data["max_experience_years"]),
    }

# -------------------------------------------------
# SCORING FUNCTION
# -------------------------------------------------

def compute_score(cand, jd, weights):
    skills = set(cand["skills"])
    req = set(jd["required_skills"])
    nice = set(jd["nice_to_have_skills"])

    # skill score
    if len(req) == 0:
        s_skill = 0.5
    else:
        hard = len(skills & req)
        soft = len(skills & nice)
        s_skill = (hard + soft * 0.5) / max(len(req) + len(nice), 1)

    # experience score
    exp = cand["experience_years"]
    if exp < jd["min_experience_years"]:
        s_exp = exp / (jd["min_experience_years"] + 1)
    elif exp > jd["max_experience_years"]:
        s_exp = 0.7
    else:
        s_exp = 1

    # projects
    s_proj = min(len(cand["projects"]), 5) / 5

    # cgpa
    s_cgpa = (cand["cgpa"] or 5) / 10

    # college
    tier_map = {"Tier 1": 1, "Tier 2": 0.75, "Tier 3": 0.5, None: 0.5}
    s_col = tier_map[cand["college_tier"]]

    score = (
        weights["skills"] * s_skill +
        weights["experience"] * s_exp +
        weights["projects"] * s_proj +
        weights["cgpa"] * s_cgpa +
        weights["college"] * s_col
    ) * 100

    return round(score, 2)

# -------------------------------------------------
# UI
# -------------------------------------------------

st.set_page_config(page_title="HirePro ATS – Qwen + Gemma", layout="wide")
st.title("🔥 HirePro ATS – AI Resume Screening")

if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "jd" not in st.session_state:
    st.session_state.jd = None
if "selected" not in st.session_state:
    st.session_state.selected = None

# LEFT SIDE
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📁 Upload Resumes")
    files = st.file_uploader("Upload multiple PDFs", accept_multiple_files=True)

    st.subheader("📝 Paste Job Description")
    jd_text = st.text_area("JD", height=180)

    st.subheader("⚙️ Weight Preferences")
    w1 = st.slider("Skills", 0.0, 1.0, 0.4)
    w2 = st.slider("Experience", 0.0, 1.0, 0.25)
    w3 = st.slider("Projects", 0.0, 1.0, 0.2)
    w4 = st.slider("CGPA", 0.0, 1.0, 0.1)
    w5 = st.slider("College Tier", 0.0, 1.0, 0.1)

    # normalize weights
    total = w1 + w2 + w3 + w4 + w5
    weights = {
        "skills": w1/total,
        "experience": w2/total,
        "projects": w3/total,
        "cgpa": w4/total,
        "college": w5/total,
    }

    if st.button("🚀 Run Screening"):
        if not files:
            st.error("Upload resumes first.")
        elif not jd_text.strip():
            st.error("Paste job description.")
        else:
            st.info("Parsing JD with Qwen3:4b...")
            jd_parsed = parse_jd(jd_text)
            st.session_state.jd = jd_parsed

            candidates = []

            for f in files:
                with st.spinner(f"Processing {f.name}"):
                    f.seek(0)
                    text1 = extract_text_pdfplumber(f)
                    f.seek(0)
                    text2 = extract_text_pymupdf(f)

                    full_text = normalize_text(text1 + "\n" + text2)
                    parsed = parse_resume(full_text)

                    parsed["id"] = str(uuid.uuid4())
                    parsed["file"] = f.name
                    candidates.append(parsed)

            # score
            for c in candidates:
                c["score"] = compute_score(c, jd_parsed, weights)

            # rerank with Gemma 1B
            prompt = RERANK_PROMPT.format(
                jd=json.dumps(jd_parsed, indent=2),
                candidates=json.dumps(candidates, indent=2)
            )
            raw = call_gemma(prompt)
            raw_clean = re.sub(r"```json|```", "", raw).strip()

            try:
                order = json.loads(raw_clean)["ordered_ids"]
                id_map = {c["id"]: c for c in candidates}
                reranked = [id_map[i] for i in order if i in id_map]
                # fallback for any missing
                for c in candidates:
                    if c["id"] not in order:
                        reranked.append(c)
            except:
                reranked = sorted(candidates, key=lambda x: x["score"], reverse=True)

            st.session_state.candidates = reranked
            st.success("Screening Complete!")

# RIGHT SIDE – TOP LIST
with col2:
    st.subheader("🏆 Top Candidates")
    cands = st.session_state.candidates

    if cands:
        top_n = st.number_input("Top N", 1, len(cands), min(5, len(cands)))
        top = cands[:top_n]

        cols = st.columns(len(top))
        for col, c in zip(cols, top):
            with col:
                if st.button(f"{c['name'] or c['file']}\n({c['score']:.1f})", key=c["id"]):
                    st.session_state.selected = c["id"]

# DETAILS
st.markdown("---")
st.header("📄 Candidate Details")

sel = st.session_state.selected
if sel:
    cand = next((x for x in st.session_state.candidates if x["id"] == sel), None)
    if cand:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.subheader("🧠 Skills")
            st.write(", ".join(cand["skills"]))

            st.subheader("🎯 CGPA")
            st.write(cand["cgpa"] or "Not found")

        with c2:
            st.subheader("💼 Experience")
            st.write(f"{cand['experience_years']} years")

            st.subheader("🎓 College")
            st.write(cand["college"])
            st.write("Tier:", cand["college_tier"])

        with c3:
            st.subheader("📊 Score")
            st.write(cand["score"])

        st.subheader("🧩 Projects")
        if cand["projects"]:
            for p in cand["projects"]:
                st.markdown(f"- **{p['title']}** – {p['summary']}")
        else:
            st.write("No projects found.")
