import streamlit as st
import uuid
import json
from utils.pdf_reader import extract_text_pdfplumber, extract_text_pymupdf
from utils.text_cleaner import normalize_text
from parser.resume_parser import parse_resume
from parser.jd_parser import parse_jd
from ranking.scoring import compute_score
from ranking.reranker import rerank_with_groq

# ----------------------------------------------------------
# Streamlit configuration
# ----------------------------------------------------------
st.set_page_config(page_title="HirePro ATS – Groq Powered", layout="wide")
st.title("🔥 HirePro ATS – AI Resume Screener (Groq)")

# Session state setup
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "selected" not in st.session_state:
    st.session_state.selected = None
if "jd" not in st.session_state:
    st.session_state.jd = None


# ----------------------------------------------------------
# LEFT SIDEBAR: Upload resumes + JD + Weights
# ----------------------------------------------------------
col1, col2 = st.columns([1.3, 1])

with col1:

    st.subheader("📁 Upload Multiple Resumes")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

    st.subheader("📝 Paste Job Description")
    jd_text = st.text_area("Job Description", height=200)

    st.subheader("⚙️ Screening Weights")
    w1 = st.slider("Skills Importance", 0.0, 1.0, 0.40)
    w2 = st.slider("Experience Importance", 0.0, 1.0, 0.25)
    w3 = st.slider("Projects Importance", 0.0, 1.0, 0.15)
    w4 = st.slider("CGPA Importance", 0.0, 1.0, 0.10)
    w5 = st.slider("College Tier Importance", 0.0, 1.0, 0.10)

    # Normalize weights
    total = w1 + w2 + w3 + w4 + w5
    weights = {
        "skills": w1 / total,
        "experience": w2 / total,
        "projects": w3 / total,
        "cgpa": w4 / total,
        "college": w5 / total,
    }

    # ----------------------------------------------------------
    # MAIN BUTTON
    # ----------------------------------------------------------
    if st.button("🚀 Run Screening"):
        if not files:
            st.error("Upload resumes first.")
            st.stop()

        if not jd_text.strip():
            st.error("Paste job description.")
            st.stop()

        st.info("🧠 Parsing Job Description with Groq...")
        jd_parsed = parse_jd(jd_text)
        st.session_state.jd = jd_parsed

        candidates = []
        st.info("📄 Processing resumes...")

        for f in files:
            with st.spinner(f"Processing {f.name}..."):
                # Extract text from PDF
                f.seek(0)
                t1 = extract_text_pdfplumber(f)
                # f.seek(0)
                # t2 = extract_text_pymupdf(f)

                resume_text = normalize_text(t1)

                # Parse resume with Groq
                parsed = parse_resume(resume_text)
                parsed["id"] = str(uuid.uuid4())
                parsed["file"] = f.name

                candidates.append(parsed)

        # Compute scores
        for c in candidates:
            c["score"] = compute_score(c, jd_parsed, weights)

        # Rerank using Groq (Mixtral / Llama3)
        st.info("⚡ Re-ranking with Groq Mixtral…")
        reranked = rerank_with_groq(jd_parsed, candidates)

        st.session_state.candidates = reranked
        st.success("🎉 Screening Complete!")


# ----------------------------------------------------------
# RIGHT SIDE: Top Candidates
# ----------------------------------------------------------
with col2:

    st.subheader("🏆 Top Candidates")

    cands = st.session_state.candidates

    if cands:
        top_n = st.number_input("Show Top N", min_value=1, max_value=len(cands), value=min(5, len(cands)))
        top = cands[:top_n]

        cols = st.columns(len(top))
        for col, c in zip(cols, top):
            with col:
                if st.button(f"{c['name'] or c['file']}\n({c['score']:.1f})", key=c["id"]):
                    st.session_state.selected = c["id"]


# ----------------------------------------------------------
# Candidate Detail Page
# ----------------------------------------------------------
st.markdown("---")
st.header("📄 Candidate Details")

selected = st.session_state.selected

if selected:
    cand = next((x for x in st.session_state.candidates if x["id"] == selected), None)

    if cand:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.subheader("🧠 Skills")
            st.write(", ".join(cand["skills"]))

            st.subheader("🎯 CGPA")
            st.write(cand["cgpa"] if cand["cgpa"] else "Not found")

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
            for p in cand.get("projects", []):
                title = p.get("title", "Untitled Project")
                summary = p.get("summary", "No summary available")
                st.markdown(f"- **{title}** – {summary}")

        else:
            st.write("No projects found.")
