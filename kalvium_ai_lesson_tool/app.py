import os, json, io, zipfile, textwrap
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from research import run_research
from lesson_engine import generate_lesson, run_research_qc, run_instructional_qc, apply_qc_recommendations
from exports import lesson_to_markdown, make_export_zip

load_dotenv()
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "saved_lessons"
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="LessonCraft AI | Kalvium Task", page_icon="📚", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.6rem;max-width:1200px}
.hero{padding:1.35rem 1.5rem;border-radius:16px;background:linear-gradient(115deg,#172554,#1d4ed8);color:white;margin-bottom:1.2rem}
.hero h1{color:white;margin:0;font-size:2rem}.hero p{color:#dbeafe;margin:.4rem 0 0}
.small-muted{color:#64748b;font-size:.88rem}
[data-testid="stMetric"]{background:#f8fafc;padding:12px;border-radius:12px}
</style>
<div class="hero"><h1>📚 LessonCraft AI</h1><p>Research-backed lesson generation · Two independent quality checks · Instructor review and export</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Google Gemini API key", value=os.getenv("GEMINI_API_KEY", ""), type="password", help="Your key stays in this local app session. You can also set GEMINI_API_KEY in a .env file.")
    model = st.text_input("Gemini model", value=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    st.caption("Research uses public search results, Open Library, Crossref and YouTube search. AI generation and both QC audits require a Gemini API key.")
    st.divider()
    st.caption("Kalvium AI Research Intern · Local prototype")
    st.divider()
    st.subheader("Saved lessons")
    saved_files = sorted(DATA_DIR.glob("*.json"))
    if saved_files:
        selected_saved = st.selectbox("Load a saved lesson", saved_files, format_func=lambda p: p.stem)
        if st.button("Load selected lesson", use_container_width=True):
            try:
                saved_record = json.loads(selected_saved.read_text(encoding="utf-8"))
                st.session_state.lesson = saved_record.get("lesson")
                st.session_state.research = saved_record.get("research")
                st.session_state.qc1 = saved_record.get("qc1")
                st.session_state.qc2 = saved_record.get("qc2")
                st.session_state.lesson_title = st.session_state.lesson.get("title", "")
                st.session_state.objective = st.session_state.lesson.get("objective", "")
                st.rerun()
            except Exception as e:
                st.error(f"Could not load saved lesson: {e}")
    else:
        st.caption("No saved lessons yet.")

if "lesson" not in st.session_state: st.session_state.lesson = None
if "research" not in st.session_state: st.session_state.research = None
if "qc1" not in st.session_state: st.session_state.qc1 = None
if "qc2" not in st.session_state: st.session_state.qc2 = None
if "lesson_title" not in st.session_state: st.session_state.lesson_title = "HTTP Requests and Responses"
if "objective" not in st.session_state: st.session_state.objective = "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."

st.subheader("1. Define the lesson")
c1, c2 = st.columns(2)
with c1:
    title = st.text_input("Lesson title", value=st.session_state.lesson_title, placeholder="e.g., HTTP Requests and Responses")
with c2:
    objective = st.text_area("Learning objective", value=st.session_state.objective, height=90, placeholder="By the end of this lesson, learners will be able to...")
st.session_state.lesson_title, st.session_state.objective = title, objective

with st.expander("Try the required sample inputs", expanded=False):
    st.write("**Kalvium sample:** HTTP Requests and Responses — Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.")
    st.write("**Suggested second test:** Python Functions — Define functions, explain parameters and return values, and write a reusable function to solve a simple problem.")
    if st.button("Load second test lesson"):
        st.session_state.lesson_title = "Python Functions"
        st.session_state.objective = "Define functions, explain parameters and return values, and write a reusable function to solve a simple problem."
        st.rerun()

st.subheader("2. Generate and validate")
col_a, col_b = st.columns([1,1])
with col_a:
    do_research = st.button("🔎 Research sources", use_container_width=True)
with col_b:
    do_generate = st.button("✨ Generate lesson + run both QC layers", type="primary", use_container_width=True)

if do_research:
    if not title.strip() or not objective.strip(): st.error("Please enter both a lesson title and a learning objective.")
    else:
        with st.spinner("Searching websites, books and YouTube resources..."):
            try:
                st.session_state.research = run_research(title, objective)
                st.success(f"Research complete: {len(st.session_state.research.get('web', []))} web sources, {len(st.session_state.research.get('books', []))} books and {len(st.session_state.research.get('youtube', []))} videos.")
            except Exception as e: st.error(f"Research failed: {e}. Your existing lesson and edits have been preserved. You can retry.")

if do_generate:
    if not title.strip() or not objective.strip(): st.error("Please enter both a lesson title and a learning objective.")
    elif not api_key.strip(): st.error("Add your Google Gemini API key in the left sidebar before generating the lesson.")
    else:
        client = genai.Client(api_key=api_key.strip())
        try:
            if not st.session_state.research:
                with st.spinner("Researching websites, books and YouTube..."):
                    st.session_state.research = run_research(title, objective)
            with st.spinner("Generating a structured 45-minute lesson..."):
                st.session_state.lesson = generate_lesson(client, model, title, objective, st.session_state.research)
                st.session_state.qc1 = None; st.session_state.qc2 = None
            with st.spinner("Running independent research accuracy audit..."):
                st.session_state.qc1 = run_research_qc(client, model, st.session_state.lesson, st.session_state.research)
            with st.spinner("Running independent instructional quality audit..."):
                st.session_state.qc2 = run_instructional_qc(client, model, st.session_state.lesson, objective)
            st.success("Lesson generated and both QC audits completed. Review the results below.")
        except Exception as e:
            st.error(f"A generation or QC step failed: {e}")
            st.info("Your last saved lesson and instructor edits are preserved. Retry the failed workflow when ready.")

if st.session_state.research:
    with st.expander("Research sources", expanded=False):
        for group, label in [("web","Websites"),("books","Books / publications"),("youtube","YouTube videos")]:
            st.markdown(f"**{label}**")
            items = st.session_state.research.get(group, [])
            if not items: st.write("No results found in this category.")
            for item in items:
                st.markdown(f"- [{item.get('title','Untitled')}]({item.get('url','#')}) — {item.get('source','')}. {item.get('snippet','')}")

if st.session_state.lesson:
    st.divider(); st.subheader("3. Instructor review and editing")
    lesson = st.session_state.lesson
    st.caption("Edit the lesson below. Changes are retained in this session and included in saved/exported files.")
    lesson["title"] = st.text_input("Lesson heading", value=lesson.get("title", title))
    lesson["objective"] = st.text_area("Learning objective", value=lesson.get("objective", objective), height=70)
    lesson["overview"] = st.text_area("Overview", value=lesson.get("overview", ""), height=90)
    sections = lesson.get("sections", [])
    edited_sections = []
    for i, section in enumerate(sections):
        with st.expander(f"{i+1}. {section.get('heading','Lesson section')} · {section.get('minutes',0)} min", expanded=(i==0)):
            heading = st.text_input("Section heading", value=section.get("heading",""), key=f"heading_{i}")
            body = st.text_area("Explanation and examples", value=section.get("content",""), height=180, key=f"body_{i}")
            activity = st.text_area("Activity / application", value=section.get("activity",""), height=90, key=f"activity_{i}")
            edited_sections.append({**section,"heading":heading,"content":body,"activity":activity})
    lesson["sections"] = edited_sections
    lesson["knowledge_check"] = st.text_area("Knowledge check", value=lesson.get("knowledge_check",""), height=150)
    lesson["takeaways"] = st.text_area("Key takeaways (one per line)", value="\n".join(lesson.get("takeaways",[])) if isinstance(lesson.get("takeaways"),list) else str(lesson.get("takeaways","")), height=100).splitlines()
    st.session_state.lesson = lesson

    if st.session_state.qc1 or st.session_state.qc2:
        st.subheader("4. Quality control audit reports")
        q1, q2 = st.columns(2)
        with q1:
            st.markdown("#### QC Layer 1 · Research & factual accuracy")
            if st.session_state.qc1:
                st.write(st.session_state.qc1.get("overall_assessment",""))
                st.metric("Issues identified", len(st.session_state.qc1.get("issues",[])))
                for issue in st.session_state.qc1.get("issues",[]):
                    st.markdown(f"- **{issue.get('severity','Review')}: {issue.get('claim','Claim')}** — {issue.get('problem','')} **Suggested fix:** {issue.get('suggestion','')}")
                st.markdown("**Source reliability:** " + st.session_state.qc1.get("source_reliability","Not assessed"))
        with q2:
            st.markdown("#### QC Layer 2 · Instructional quality")
            if st.session_state.qc2:
                st.write(st.session_state.qc2.get("overall_assessment",""))
                st.metric("Issues identified", len(st.session_state.qc2.get("issues",[])))
                for issue in st.session_state.qc2.get("issues",[]):
                    st.markdown(f"- **{issue.get('criterion','Criterion')}** — {issue.get('problem','')} **Suggested fix:** {issue.get('suggestion','')}")
                st.markdown("**Objective alignment:** " + st.session_state.qc2.get("objective_alignment","Not assessed"))
        st.caption("The two audits use separate prompts and produce separate reports. Treat AI QC as decision support; verify important claims against the cited primary sources.")
        if st.button("Apply suitable QC recommendations to lesson", use_container_width=True):
            if not api_key.strip():
                st.error("Add your Google Gemini API key in the sidebar to apply recommendations.")
            else:
                try:
                    with st.spinner("Applying both QC reports while preserving the 45-minute lesson structure..."):
                        revised = apply_qc_recommendations(genai.Client(api_key=api_key.strip()), model, lesson, st.session_state.qc1, st.session_state.qc2)
                    st.session_state.lesson = revised
                    st.success("QC recommendations applied. Review the revised lesson before exporting.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not apply recommendations: {e}. Your current edits are preserved.")

    st.subheader("5. Save, preview and export")
    markdown = lesson_to_markdown(lesson, st.session_state.research or {})
    st.markdown("#### Final lesson preview")
    st.markdown(markdown)
    safe_name = "".join(ch.lower() if ch.isalnum() else "_" for ch in lesson.get("title","lesson"))[:60].strip("_") or "lesson"
    if st.button("💾 Save lesson locally"):
        record = {"saved_at":datetime.now().isoformat(timespec="seconds"),"lesson":lesson,"research":st.session_state.research,"qc1":st.session_state.qc1,"qc2":st.session_state.qc2}
        (DATA_DIR / f"{safe_name}.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
        st.success(f"Saved to saved_lessons/{safe_name}.json")
    st.download_button("⬇️ Download lesson (Markdown)", data=markdown, file_name=f"{safe_name}.md", mime="text/markdown")
    bundle = make_export_zip(lesson, st.session_state.research or {}, st.session_state.qc1, st.session_state.qc2)
    st.download_button("📦 Export complete package (lesson + references + QC reports)", data=bundle, file_name=f"{safe_name}_kalvium_submission_artifacts.zip", mime="application/zip", type="primary")
else:
    st.info("Start by entering a lesson title and learning objective, then click Research sources or Generate lesson + run both QC layers.")

st.divider()
st.markdown("<p class='small-muted'>Prototype note: Research availability depends on internet access and public source endpoints. AI generation and QC require a valid Google Gemini API key (free-tier availability and limits apply). No deployment is required; run locally with Streamlit.</p>", unsafe_allow_html=True)
