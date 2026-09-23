import streamlit as st
import os
import tempfile
from database.db_manager import (
    init_db, get_all_candidates, create_candidate, update_base_resume,
    save_job_session, get_candidate_sessions
)
from tools.parser import ResumeParserTool
from tools.document_exporter import DocumentExporter
from crew import build_resume_tailor_crew

init_db()

st.set_page_config(page_title="In-House AI Resume Workspace", page_icon="👥", layout="wide")

st.title("👥 Multi-Candidate AI Resume & Intelligence Workspace")
st.caption("Manage candidate profiles, research target companies, and track tailored resume generations.")

with st.sidebar:
    st.header("🗂️ Candidate Workspaces")
    
    candidates = get_all_candidates()
    candidate_names = [c["name"] for c in candidates]
    
    selected_candidate_name = st.selectbox("Select Candidate Session", ["-- Add New Candidate --"] + candidate_names)
    
    if selected_candidate_name == "-- Add New Candidate --":
        new_name = st.text_input("New Candidate Name", placeholder="e.g. Person A")
        if st.button("Create Candidate Profile"):
            if new_name.strip():
                cid = create_candidate(new_name.strip())
                if cid:
                    st.success(f"Candidate '{new_name}' created!")
                    st.rerun()
                else:
                    st.error("Candidate name already exists.")
            else:
                st.warning("Please enter a valid name.")
        candidate = None
    else:
        candidate = next(c for c in candidates if c["name"] == selected_candidate_name)

    st.markdown("---")
    st.header("🔑 Provider & API Settings")
    
    llm_provider = st.selectbox("Select LLM Provider", ["openai", "huggingface", "ollama"])
    
    openai_key = ""
    hf_key = ""
    custom_model = ""
    
    if llm_provider == "openai":
        openai_key = st.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    elif llm_provider == "huggingface":
        hf_key = st.text_input("Hugging Face User Token", type="password", value=os.environ.get("HUGGINGFACE_API_KEY", ""))
        custom_model = st.text_input("HF Model Repo", value="huggingface/meta-llama/Meta-Llama-3-8B-Instruct")
    elif llm_provider == "ollama":
        custom_model = st.text_input("Ollama Model Name", value="ollama/llama3")
        st.info("Ensure Ollama service is running locally at http://localhost:11434")

    tavily_key = st.text_input("Tavily API Key", type="password", value=os.environ.get("TAVILY_API_KEY", ""))

if candidate:
    st.subheader(f"Workspace: {candidate['name']}")
    
    tab1, tab2 = st.tabs(["🚀 New Job Adaptation", "📂 Historical Sessions & Archives"])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("#### 1. Candidate Base Resume")
            current_resume_text = candidate["base_resume_text"] or ""
            
            uploaded_file = st.file_uploader(
                "Upload/Update Resume (PDF, DOCX, PNG, JPG)",
                type=["pdf", "docx", "doc", "png", "jpg", "jpeg"],
                key=f"upload_{candidate['id']}"
            )
            
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                parsed_text = ResumeParserTool.parse_file(tmp_path)
                os.remove(tmp_path)
                
                if st.button("Save Parsed Text as Base Resume"):
                    update_base_resume(candidate["id"], parsed_text)
                    st.success("Base resume updated successfully!")
                    st.rerun()

            if current_resume_text:
                st.success("✓ Base resume loaded in workspace.")
                with st.expander("View Base Resume Text"):
                    st.text_area("Extracted Resume Content", current_resume_text, height=150, disabled=True)
            else:
                st.warning("No base resume loaded. Please upload a resume file.")

            st.markdown("#### 2. Target Job Details")
            input_type = st.radio("Input Method", ["Job URL", "Direct Copy/Paste Job Description"], horizontal=True, key=f"mode_{candidate['id']}")

            job_url = ""
            job_text = ""
            company_hint = ""

            if input_type == "Job URL":
                job_url = st.text_input("Job Posting URL", placeholder="https://...", key=f"url_{candidate['id']}")
            else:
                job_text = st.text_area("Job Description Text", height=200, placeholder="Paste role requirements...", key=f"text_{candidate['id']}")
                company_hint = st.text_input("Company Name (Optional)", placeholder="e.g. Stripe", key=f"comp_{candidate['id']}")

            run_btn = st.button("✨ Tailor Resume & Research Company", type="primary", use_container_width=True, key=f"run_{candidate['id']}")

        with col2:
            st.markdown("#### 3. Output & Intelligence Report")
            
            if run_btn:
                if not tavily_key:
                    st.error("Please supply a Tavily API Key in the sidebar.")
                elif llm_provider == "openai" and not openai_key:
                    st.error("Please supply an OpenAI API Key.")
                elif llm_provider == "huggingface" and not hf_key:
                    st.error("Please supply a Hugging Face Access Token.")
                elif not current_resume_text:
                    st.error("Please upload and save a base resume first.")
                elif input_type == "Job URL" and not job_url.strip():
                    st.error("Please enter a job URL.")
                elif input_type == "Direct Copy/Paste Job Description" and not job_text.strip():
                    st.error("Please paste the job description text.")
                else:
                    os.environ["TAVILY_API_KEY"] = tavily_key
                    if openai_key:
                        os.environ["OPENAI_API_KEY"] = openai_key
                    if hf_key:
                        os.environ["HUGGINGFACE_API_KEY"] = hf_key

                    with st.status("🤖 Executing multi-agent workflow...", expanded=True) as status:
                        try:
                            is_url = (input_type == "Job URL")
                            job_input = job_url if is_url else job_text

                            status.write("🌐 Scraping posting & conducting company web research...")
                            crew = build_resume_tailor_crew(
                                resume_text=current_resume_text,
                                job_input=job_input,
                                is_url=is_url,
                                company_name_hint=company_hint,
                                provider=llm_provider,
                                custom_llm_model=custom_model
                            )
                            
                            status.write("🎯 Matching skills & drafting ATS resume...")
                            raw_result = crew.kickoff()
                            markdown_output = str(raw_result)

                            save_job_session(
                                candidate_id=candidate["id"],
                                job_title="Target Role",
                                company_name=company_hint or "Target Company",
                                job_input=job_input,
                                company_intel="Generated via CrewAI Research Agent",
                                tailored_markdown=markdown_output
                            )

                            docx_path = DocumentExporter.export_to_docx(markdown_output, f"Tailored_Resume_{candidate['name']}.docx")
                            pdf_path = DocumentExporter.export_to_pdf(markdown_output, f"Tailored_Resume_{candidate['name']}.pdf")

                            status.update(label="✅ Success! Adaptation saved to database.", state="complete", expanded=False)

                            st.markdown("### Generated ATS Resume")
                            st.markdown(markdown_output)

                            st.markdown("---")
                            dl1, dl2 = st.columns(2)
                            with dl1:
                                with open(docx_path, "rb") as f:
                                    st.download_button("Download DOCX", f, file_name=f"Resume_{candidate['name']}.docx", use_container_width=True)
                            with dl2:
                                with open(pdf_path, "rb") as f:
                                    st.download_button("Download PDF", f, file_name=f"Resume_{candidate['name']}.pdf", use_container_width=True)

                        except Exception as e:
                            status.update(label="❌ Pipeline execution failed", state="error")
                            st.error(str(e))

    with tab2:
        st.markdown(f"#### Past Adaptations & Sessions for {candidate['name']}")
        sessions = get_candidate_sessions(candidate["id"])
        
        if not sessions:
            st.info("No past job adaptation sessions found for this candidate yet.")
        else:
            for session in sessions:
                with st.expander(f"Session #{session['id']} — {session['company_name']} ({session['created_at']})"):
                    st.markdown(f"**Target Company:** {session['company_name']}")
                    st.markdown("---")
                    st.markdown(session["tailored_resume_markdown"])
else:
    st.info("👈 Please select an existing candidate profile or create a new candidate session in the sidebar to begin.")