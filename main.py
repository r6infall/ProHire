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
st.set_page_config(
    page_title="HirePro – Smart Hiring Solution",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------------
# Custom CSS Styling
# ----------------------------------------------------------
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Global Styles */
    .main {
        padding-top: 0rem;
        padding-bottom: 2rem;
        background: linear-gradient(135deg, #cce8bd 0%, #e6f5f8 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #cce8bd 0%, #e6f5f8 100%);
    }
    
    .block-container {
        background: transparent;
    }
    
    /* Navigation Bar */
    .navbar {
        
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 3rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 60px;
        max-width: 1300px;
        margin: 0.5rem auto;
        box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
        position: sticky;
        top: -100px;
        z-index: 1000;
    }
    
    .navbar-brand {
        font-weight: 700;
        font-size: 1.25rem;
        color: #1a1a1a;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    
    .navbar-brand .icon {
        font-size: 1.5rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #6366f1;
        width: 32px;
        height: 32px;
        background: #f5f5f5;
        border-radius: 50%;
    }
    
    .navbar-center {
        display: flex;
        gap: 2.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        color: #6b7280;
    }
    
    .navbar-center .nav-link {
        cursor: pointer;
        transition: all 0.2s ease;
        padding: 8px 16px;
        border-radius: 20px;
    }
    
    .navbar-center .nav-link:hover {
        color: #1a1a1a;
        background: #f0f0f0;
    }
    
    .navbar-center .nav-link[data-nav="home"] {
        background: #e0e0e0;
        color: #1a1a1a;
    }
    
    .navbar-right-btn {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        color: #fff;
        padding: 0.65rem 1.6rem;
        border-radius: 24px;
        font-weight: 600;
        font-size: 0.9rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 12px rgba(124, 58, 237, 0.25);
    }
    
    .navbar-right-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.35);
    }
    
    /* Landing Page Section */
    .landing-section {
        background: linear-gradient(135deg, #cce8bd 0%, #e6f5f8 100%);
        padding: 80px 40px;
        border-radius: 30px;
        margin: 30px auto;
        max-width: 1200px;
        text-align: center;
    }
    
    .landing-tag {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #1a1a1a;
        color: white;
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 14px;
        margin-bottom: 20px;
    }
    
    .landing-heading {
        font-size: 48px;
        font-weight: 700;
        color: #1a1a1a;
        margin: 20px 0;
        line-height: 1.2;
    }
    
    .landing-subheading {
        font-size: 18px;
        color: #4a4a4a;
        margin: 20px 0 40px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .landing-buttons {
        display: flex;
        gap: 15px;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .btn-primary {
        background: #1a1a1a;
        color: white;
        padding: 14px 32px;
        border-radius: 25px;
        border: none;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .btn-primary:hover {
        background: #333;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .btn-secondary {
        background: white;
        color: #1a1a1a;
        padding: 14px 32px;
        border-radius: 25px;
        border: 2px solid #1a1a1a;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .btn-secondary:hover {
        background: #f5f5f5;
        transform: translateY(-2px);
    }
    
    /* Dashboard Section */
    .dashboard-section {
        max-width: 1200px;
        margin: 40px auto;
        padding: 0 20px;
    }
    
    .dashboard-container {
        display: grid;
        grid-template-columns: 1.3fr 1fr;
        gap: 30px;
        margin-top: 30px;
    }
    
    .dashboard-panel {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.08);
    }
    
    .panel-title {
        font-size: 18px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 15px;
    }
    
    .input-box {
        background: #f8f9fa;
        border: 2px dashed #cce8bd;
        border-radius: 15px;
        padding: 20px;
        min-height: 200px;
        margin-bottom: 20px;
    }
    
    .slider-container {
        margin: 20px 0;
    }
    
    .slider-label {
        font-size: 14px;
        font-weight: 500;
        color: #4a4a4a;
        margin-bottom: 10px;
        display: block;
    }
    
    .upload-box {
        background: #f8f9fa;
        border: 2px dashed #cce8bd;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        margin-bottom: 20px;
        min-height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .candidates-box {
        background: #f8f9fa;
        border: 2px solid #e6f5f8;
        border-radius: 15px;
        padding: 30px;
        min-height: 400px;
        margin-top: 20px;
    }
    
    .candidate-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .candidate-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        border-color: #cce8bd;
    }
    
    .candidate-name {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 5px;
    }
    
    .candidate-score {
        font-size: 14px;
        color: #764ba2;
        font-weight: 500;
    }
    
    /* Streamlit component overrides */
    .stTextArea > div > div > textarea {
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        background: #f8f9fa !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #cce8bd !important;
        box-shadow: 0 0 0 3px rgba(204, 232, 189, 0.1) !important;
    }
    
    .stSlider > div {
        margin: 10px 0;
    }
    
    .stSlider > div > div > div {
        background: #cce8bd !important;
    }
    
    .stFileUploader > div {
        border: 2px dashed #cce8bd !important;
        border-radius: 15px !important;
        background: #f8f9fa !important;
        padding: 20px !important;
    }
    
    /* Styled Streamlit Components */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
    }
    
    .stSlider {
        margin: 15px 0;
    }
    
    .stButton>button {
        border-radius: 25px;
        background: #764ba2;
        color: white;
        border: none;
        padding: 12px 32px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: #5a3a7a;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .dashboard-container {
            grid-template-columns: 1fr;
        }
        
        .landing-heading {
            font-size: 32px;
        }
        
        .navbar {
            flex-direction: column;
            gap: 15px;
            padding: 20px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Session state setup
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "selected" not in st.session_state:
    st.session_state.selected = None
if "jd" not in st.session_state:
    st.session_state.jd = None
if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# ----------------------------------------------------------
# Navigation Bar
# ----------------------------------------------------------
# Create navbar HTML structure
st.markdown("""
<div class="navbar">
    <div class="navbar-brand">
        <span class="icon">⬢</span>HirePro
    </div>
    <div class="navbar-center">
        <span class="nav-link" data-nav="home">Home</span>
        <span class="nav-link" data-nav="company">Company</span>
        <span class="nav-link" data-nav="service">Service</span>
        <span class="nav-link" data-nav="resources">Resources</span>
        <span class="nav-link" data-nav="about">About us</span>
    </div>
    <button class="navbar-right-btn" id="get-started-btn">Get Started</button>
</div>
""", unsafe_allow_html=True)

# Create hidden Streamlit buttons for navigation (placed in hidden container)
with st.container():
    st.markdown("""
    <div style="display: none;">
    """, unsafe_allow_html=True)
    if st.button("", key="nav_home_btn"):
        st.session_state.current_page = "home"
        st.session_state.show_dashboard = False
        st.rerun()
    if st.button("", key="nav_company_btn"):
        st.session_state.current_page = "company"
        st.rerun()
    if st.button("", key="nav_service_btn"):
        st.session_state.current_page = "service"
        st.rerun()
    if st.button("", key="nav_resources_btn"):
        st.session_state.current_page = "resources"
        st.rerun()
    if st.button("", key="nav_about_btn"):
        st.session_state.current_page = "about"
        st.rerun()
    if st.button("", key="nav_get_started_btn"):
        st.session_state.current_page = "dashboard"
        st.session_state.show_dashboard = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Style the navbar and add interactivity
st.markdown("""
<style>
    /* Hide hidden buttons */
    button[key="nav_home_btn"],
    button[key="nav_company_btn"],
    button[key="nav_service_btn"],
    button[key="nav_resources_btn"],
    button[key="nav_about_btn"],
    button[key="nav_get_started_btn"] {
        display: none !important;
    }
    
    /* Ensure navbar is properly displayed */
    .navbar {
        position: relative !important;
        z-index: 1000 !important;
    }
</style>

<script>
    // Connect navbar links to Streamlit buttons
    document.querySelector('.nav-link[data-nav="home"]').addEventListener('click', function() {
        document.querySelector('button[key="nav_home_btn"]').click();
    });
    document.querySelector('.nav-link[data-nav="company"]').addEventListener('click', function() {
        document.querySelector('button[key="nav_company_btn"]').click();
    });
    document.querySelector('.nav-link[data-nav="service"]').addEventListener('click', function() {
        document.querySelector('button[key="nav_service_btn"]').click();
    });
    document.querySelector('.nav-link[data-nav="resources"]').addEventListener('click', function() {
        document.querySelector('button[key="nav_resources_btn"]').click();
    });
    document.querySelector('.nav-link[data-nav="about"]').addEventListener('click', function() {
        document.querySelector('button[key="nav_about_btn"]').click();
    });
    document.getElementById('get-started-btn').addEventListener('click', function() {
        document.querySelector('button[key="nav_get_started_btn"]').click();
    });
</script>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# Landing Page Section
# ----------------------------------------------------------
if not st.session_state.show_dashboard:
    st.markdown("""
    <div class="landing-section">
        <div class="landing-tag">
            <span style="background: white; color: #1a1a1a; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">New</span>
            <span>Your Smart Hiring Companion</span>
            <span>→</span>
        </div>
        <h1 class="landing-heading">Reduce Hiring Time. Reduce Bias. Improve Decisions with HirePro</h1>
        <p class="landing-subheading">Empowering you to take charge of your hiring process with intuitive tools and AI-powered insights.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Landing page buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col2:
        if st.button("Get Started →", use_container_width=True, key="landing_get_started"):
            st.session_state.show_dashboard = True
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    btn_col4, btn_col5, btn_col6 = st.columns([1, 1, 1])
    with btn_col5:
        if st.button("Explore Features", use_container_width=True, key="landing_explore"):
            st.session_state.show_dashboard = True
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    st.markdown("""
    <style>
        button[key="landing_get_started"] {
            background: #1a1a1a !important;
            color: white !important;
            border-radius: 25px !important;
            padding: 14px 32px !important;
            font-size: 16px !important;
            font-weight: 500 !important;
        }
        
        button[key="landing_explore"] {
            background: white !important;
            color: #1a1a1a !important;
            border: 2px solid #1a1a1a !important;
            border-radius: 25px !important;
            padding: 14px 32px !important;
            font-size: 16px !important;
            font-weight: 500 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------
# Dashboard Section
# ----------------------------------------------------------
if st.session_state.show_dashboard:
    st.markdown('<div id="dashboard"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="dashboard-section">
        <div class="dashboard-container">
    """, unsafe_allow_html=True)
    
    # Left Panel
    with st.container():
        st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
        
        st.markdown('<div class="panel-title">Job Description</div>', unsafe_allow_html=True)
        jd_text = st.text_area(
            "Component for putting the job description",
            height=200,
            label_visibility="collapsed",
            placeholder="Enter job description here..."
        )
        
        st.markdown("""
        <div class="slider-container">
            <div class="slider-label">Skills Importance</div>
        </div>
        """, unsafe_allow_html=True)
        w1 = st.slider("", 0.0, 1.0, 0.40, label_visibility="collapsed", key="skills_slider")
        
        st.markdown("""
        <div class="slider-container">
            <div class="slider-label">Experience Importance</div>
        </div>
        """, unsafe_allow_html=True)
        w2 = st.slider("", 0.0, 1.0, 0.25, label_visibility="collapsed", key="exp_slider")
        
        st.markdown("""
        <div class="slider-container">
            <div class="slider-label">CGPA Importance</div>
        </div>
        """, unsafe_allow_html=True)
        w4 = st.slider("", 0.0, 1.0, 0.10, label_visibility="collapsed", key="cgpa_slider")
        
        st.markdown('<div class="panel-title" style="margin-top: 25px;">Add further must-haves</div>', unsafe_allow_html=True)
        additional_reqs = st.text_area(
            "Component for having additional requirements",
            height=100,
            label_visibility="collapsed",
            placeholder="Enter additional requirements..."
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Right Panel
    with st.container():
        st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
        
        st.markdown('<div class="panel-title">Add resume</div>', unsafe_allow_html=True)
        files = st.file_uploader(
            "Component for uploading multiple resume",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="Upload multiple PDF resumes"
        )
        
        # Normalize weights (adding default values for projects and college)
        w3 = 0.15  # Projects importance (default)
        w5 = 0.10  # College tier importance (default)
        total = w1 + w2 + w3 + w4 + w5
        if total > 0:
            weights = {
                "skills": w1 / total,
                "experience": w2 / total,
                "projects": w3 / total,
                "cgpa": w4 / total,
                "college": w5 / total,
            }
        else:
            weights = {
                "skills": 0.40,
                "experience": 0.25,
                "projects": 0.15,
                "cgpa": 0.10,
                "college": 0.10,
            }
        
        # Main Screening Button
        if st.button("🚀 Run Screening", use_container_width=True):
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
                    f.seek(0)
                    t1 = extract_text_pdfplumber(f)
                    resume_text = normalize_text(t1)
                    
                    parsed = parse_resume(resume_text)
                    parsed["id"] = str(uuid.uuid4())
                    parsed["file"] = f.name
                    candidates.append(parsed)
            
            # Compute scores
            for c in candidates:
                c["score"] = compute_score(c, jd_parsed, weights)
            
            # Rerank using Groq
            st.info("⚡ Re-ranking with Groq Mixtral…")
            reranked = rerank_with_groq(jd_parsed, candidates)
            
            st.session_state.candidates = reranked
            st.success("🎉 Screening Complete!")
        
        st.markdown('<div class="panel-title" style="margin-top: 30px;">Your top-k Candidates are:</div>', unsafe_allow_html=True)
        
        cands = st.session_state.candidates
        if cands:
            top_n = st.number_input(
                "Show Top N",
                min_value=1,
                max_value=len(cands),
                value=min(5, len(cands)),
                label_visibility="visible"
            )
            top = cands[:top_n]
            
            for c in top:
                st.markdown(f"""
                <div class="candidate-card">
                    <div class="candidate-name">{c.get('name', c.get('file', 'Unknown'))}</div>
                    <div class="candidate-score">Score: {c.get('score', 0):.1f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details", key=f"view_{c['id']}", use_container_width=True):
                    st.session_state.selected = c["id"]
                    st.rerun()
        else:
            st.markdown("""
            <div class="candidates-box" style="display: flex; align-items: center; justify-content: center; color: #999;">
                <p>Upload resumes and run screening to see top candidates here.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # ----------------------------------------------------------
    # Candidate Detail Section
    # ----------------------------------------------------------
    selected = st.session_state.selected
    if selected:
        st.markdown("---")
        st.markdown('<h2 style="color: #1a1a1a; margin: 30px 0;">📄 Candidate Details</h2>', unsafe_allow_html=True)
        
        cand = next((x for x in st.session_state.candidates if x["id"] == selected), None)
        
        if cand:
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
                st.subheader("🧠 Skills")
                st.write(", ".join(cand.get("skills", [])))
                
                st.subheader("🎯 CGPA")
                st.write(cand.get("cgpa", "Not found") if cand.get("cgpa") else "Not found")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c2:
                st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
                st.subheader("💼 Experience")
                st.write(f"{cand.get('experience_years', 0)} years")
                
                st.subheader("🎓 College")
                st.write(cand.get("college", "Not found"))
                st.write("Tier:", cand.get("college_tier", "Not determined"))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c3:
                st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
                st.subheader("📊 Score")
                st.metric("", f"{cand.get('score', 0):.1f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="dashboard-panel" style="margin-top: 20px;">', unsafe_allow_html=True)
            st.subheader("🧩 Projects")
            if cand.get("projects"):
                for p in cand.get("projects", []):
                    title = p.get("title", "Untitled Project")
                    summary = p.get("summary", "No summary available")
                    st.markdown(f"- **{title}** – {summary}")
            else:
                st.write("No projects found.")
            st.markdown('</div>', unsafe_allow_html=True)


