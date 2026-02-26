
# import streamlit as st
# import pdfplumber
# import fitz  
# import re
# import json
# import numpy as np
# import pandas as pd
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv
# from rapidfuzz import fuzz, process

# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# def extract_text_pdfplumber(file_bytes):
#     text = []
#     with pdfplumber.open(file_bytes) as pdf:
#         for page in pdf.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text.append(page_text)
#     return "\n".join(text)


# def extract_text_pymupdf(file_bytes):
#     file_bytes.seek(0)
#     text = []
#     doc = fitz.open(stream=file_bytes.read(), filetype="pdf")
#     for page in doc:
#         text.append(page.get_text("text"))
#     return "\n".join(text)



# # -----------------------------------------
# # Canonical Skills
# # -----------------------------------------
# CANONICAL_SKILLS = [
#     "machine learning", "deep learning", "python", "tensorflow", "pytorch",
#     "nlp", "computer vision", "sql", "aws", "docker", "kubernetes",
#     "data analysis", "pandas", "numpy", "scikit-learn", "git", "rest api",
#     "java", "c++", "javascript", "node.js", "html", "css",
#     "data structures", "algorithms"
# ]

# # -----------------------------------------
# # Synonyms → Canonical Skills
# # -----------------------------------------
# SKILL_SYNONYMS = {
#     "ml": "machine learning",
#     "ml engineer": "machine learning",
#     "machine-learning": "machine learning",
#     "deep-learning": "deep learning",
#     "dl": "deep learning",
#     "tensor flow": "tensorflow",
#     "tensor-flow": "tensorflow",
#     "tf": "tensorflow",
#     "reactjs": "react",
#     "react.js": "react",
#     "js": "javascript",
#     "nodejs": "node.js",
#     "node.js": "node.js",
#     "k8s": "kubernetes",
#     "aws cloud": "aws",
#     "cplusplus": "c++",
#     "cpp": "c++",
# }

# # -----------------------------------------
# # ROLE → SKILLSET Expansion
# # -----------------------------------------
# ROLE_SKILLS = {
#     "ml engineer": ["machine learning", "deep learning", "python", "tensorflow", "pytorch"],
#     "data scientist": ["machine learning", "python", "sql", "data analysis"],
#     "sde": ["java", "python", "data structures", "algorithms"],
#     "backend developer": ["node.js", "sql", "docker"],
#     "frontend developer": ["javascript", "react", "html", "css"],
# }

# # -----------------------------------------
# # Utility: normalize text
# # -----------------------------------------
# def normalize_text_simple(s):
#     if not s:
#         return ""
#     s = s.lower()
#     s = re.sub(r"[\s\-_\/]+", " ", s)
#     return s.strip()

# def normalize_skill_term(skill):
#     s = normalize_text_simple(skill)

#     # check synonyms
#     for k, v in SKILL_SYNONYMS.items():
#         if s == k or k in s:
#             return v

#     # remove trailing job role words
#     s = re.sub(r"\b(developer|engineer|intern|jr|senior|lead)\b", "", s).strip()
#     s = re.sub(r"\s+", " ", s)

#     return s.strip()

# # -----------------------------------------
# # Strong LLM Prompt
# # -----------------------------------------
# LLM_PROMPT_TEMPLATE = """
# Extract ONLY skills and achievements from the following resume text.

# Return a STRICT JSON object like this:
# {{
#   "skills": ["python", "machine learning"],
#   "achievements": ["Improved accuracy by 20%"]
# }}

# Rules:
# - Skills must be 1–3 word tokens.
# - Achievements must be short bullet-like statements.
# - Normalize synonyms automatically.
# - Return ONLY JSON. No explanations.

# Resume:
# ---
# {resume}
# ---
# """

# # -----------------------------------------
# # Safe Gemini Call
# # -----------------------------------------
# def call_llm(prompt):
#     try:
#         model = genai.GenerativeModel("gemini-2.0-flash")
#         response = model.generate_content(prompt)

#         text = response.text.strip()
#         text = re.sub(r"^```(json)?", "", text)
#         text = re.sub(r"```$", "", text)
#         print("gemini_response")
#         # Try direct JSON
#         try:
#             return json.loads(text)
#         except:
#             match = re.search(r"\{.*\}", text, re.DOTALL)
#             if match:
#                 return json.loads(match.group(0))

#         return None
#     except Exception as e:
#         return None

# # -----------------------------------------
# # Fallback skill extractor
# # -----------------------------------------
# def regex_skill_fallback(text, canonical):
#     text = text.lower()
#     tokens = canonical + list(SKILL_SYNONYMS.keys())
#     tokens = sorted(tokens, key=len, reverse=True)
#     pattern = r"\b(" + "|".join(map(re.escape, tokens)) + r")\b"
#     found = re.findall(pattern, text)
#     found = [normalize_skill_term(f) for f in found]
#     return list(dict.fromkeys(found))

# # -----------------------------------------
# # Extract using LLM + fallback + normalization
# # -----------------------------------------
# def extract_skills_and_achievements(resume_text):
#     prompt = LLM_PROMPT_TEMPLATE.format(resume=resume_text)
#     response = call_llm(prompt)

#     used_fallback = False
#     achievements = []

#     if response and isinstance(response, dict):
#         raw_skills = response.get("skills", [])
#         achievements = response.get("achievements", [])
#     else:
#         used_fallback = True
#         raw_skills = regex_skill_fallback(resume_text, CANONICAL_SKILLS)

#     clean = []
#     for s in raw_skills:
#         if not isinstance(s, str):
#             continue
#         s = normalize_skill_term(s)
#         if len(s.split()) <= 4:
#             clean.append(s)

#     # Expand roles
#     expanded = []
#     for s in clean:
#         if s in ROLE_SKILLS:
#             expanded.extend(ROLE_SKILLS[s])

#     clean.extend(expanded)
#     clean = list(dict.fromkeys(clean))

#     achievements = [normalize_text_simple(a) for a in achievements if isinstance(a, str)]

#     return clean, achievements, used_fallback

# # -----------------------------------------
# # SBERT Model
# # -----------------------------------------
# @st.cache_resource
# def load_sbert():
#     try:
#         return SentenceTransformer("all-MiniLM-L6-v2")
#     except:
#         return None

# SBERT = load_sbert()

# @st.cache_resource
# @st.cache_resource
# def embed_canonical(_model, canonical_list):
#     if _model is None:
#         return canonical_list, None
#     norm = [normalize_skill_term(s) for s in canonical_list]
#     emb = _model.encode(norm, convert_to_numpy=True)
#     return norm, emb


# CANON_NORM, CANON_EMB = embed_canonical(SBERT, CANONICAL_SKILLS)

# def normalize_text(s):
#     if not s:
#         return ""
#     s = re.sub(r"\s+", " ", s)
#     return s.strip()

# # -----------------------------------------
# # Matching: synonym → semantic → fuzzy
# # -----------------------------------------
# def match_skill(skill):
#     sk = normalize_skill_term(skill)

#     # direct canonical match
#     if sk in CANONICAL_SKILLS:
#         return sk, 100, "exact"

#     # synonym
#     for k, v in SKILL_SYNONYMS.items():
#         if k == sk or k in sk:
#             if v in CANONICAL_SKILLS:
#                 return v, 95, "synonym"
#             return v, 80, "synonym"

#     # semantic
#     if SBERT:
#         emb = SBERT.encode([sk], convert_to_numpy=True)
#         sims = cosine_similarity(emb, CANON_EMB)[0]
#         idx = int(np.argmax(sims))
#         sim = float(sims[idx])
#         if sim >= 0.55:
#             return CANON_NORM[idx], sim * 100, "semantic"

#     # fuzzy
#     cand = process.extractOne(sk, CANONICAL_SKILLS, scorer=fuzz.partial_ratio)
#     if cand and cand[1] >= 70:
#         return cand[0], cand[1], "fuzzy"

#     return None, 0, "none"

# # -----------------------------------------
# # Scoring System
# # -----------------------------------------
# def calculate_score(required, resume_mapped, extras):
#     required = [normalize_skill_term(s) for s in required]
#     required = list(dict.fromkeys(required))

#     per_skill = 80 / max(1, len(required))
#     matched_points = 0

#     for req in required:
#         for canon, v in resume_mapped.items():
#             if fuzz.partial_ratio(req, canon) >= 75:
#                 matched_points += per_skill * (v["score"] / 100)
#                 break

#     extra_bonus = min(20, len(extras) * 3)
#     avg = np.mean([v["score"] for v in resume_mapped.values()]) if resume_mapped else 0
#     bonus = (avg / 100) * 5

#     final = int(np.clip(matched_points + extra_bonus + bonus, 1, 100))
#     breakdown = {
#         "matched_points": matched_points,
#         "extra_bonus": extra_bonus,
#         "proficiency_bonus": bonus,
#         "final_score": final
#     }
#     return final, breakdown

# # ============================================================
# # STREAMLIT UI
# # ============================================================
# st.set_page_config(page_title="HirePro – Resume Skill Matcher", layout="wide")
# st.title("🔥 HirePro – Resume Parser & Skill Matcher")

# col1, col2 = st.columns([1,1])
# with col1:
#     uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
#     jd_text = st.text_area("Paste Job Description (comma-separated skills)")

# with col2:
#     semantic_threshold = st.slider("Semantic threshold", 50, 95, 60)
#     fuzzy_threshold = st.slider("Fuzzy threshold", 50, 95, 72)

# if st.button("Process Resume"):
#     if not uploaded:
#         st.error("Please upload a resume.")
#         st.stop()

#     uploaded.seek(0)
#     text1 = extract_text_pdfplumber(uploaded)

#     uploaded.seek(0)
#     text2 = extract_text_pymupdf(uploaded)

#     resume_text = normalize_text(text1 + "\n" + text2)

#     # st.subheader("📄 Extracted Resume Text")
#     # st.write(resume_text[:2000] + "...")


#     # ---------- Extract using LLM ----------
#     skills, achievements, fallback = extract_skills_and_achievements(resume_text)

#     if fallback:
#         st.warning("⚠️ LLM failed → Using fallback regex extractor.")

#     st.subheader("🧠 Extracted Skills")
#     st.write(skills)

#     st.subheader("🏆 Achievements")
#     st.write(achievements)


#     # ---------- Parse JD ----------
#     if "," in jd_text:
#         required = [s.strip().lower() for s in jd_text.split(",")]
#     else:
#         required = [s.strip().lower() for s in jd_text.split("\n")]

#     # ---------- Match ----------
#     mapped = {}
#     extras = []

#     for s in skills:
#         canon, score, method = match_skill(s)
#         if canon:
#             if canon not in mapped or score > mapped[canon]["score"]:
#                 mapped[canon] = {"original": s, "score": score, "method": method}
#         else:
#             extras.append(s)

#     # ---------- Score ----------
#     final, breakdown = calculate_score(required, mapped, extras)

#     st.metric("⭐ Final Skill Match Score", f"{final}/100")
#     st.json(breakdown)

#     st.subheader("🔍 Mapped Skills")
#     st.dataframe(pd.DataFrame([
#         {"canonical": k, "original": v["original"], "score": v["score"], "method": v["method"]}
#         for k, v in mapped.items()
#     ]))

#     st.subheader("➕ Extra Resume Skills")
#     st.write(extras)


# # HirePro\Scripts\activate
