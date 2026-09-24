import os
import argparse
from tools.parser import ResumeParserTool
from tools.document_exporter import DocumentExporter
from database.db_manager import init_db, create_candidate, get_all_candidates, save_job_session
from crew import build_resume_tailor_crew

def run_cli():
    # Initialize SQLite database schema
    init_db()

    print("==================================================")
    print("  In-House AI Resume Tailoring System (CLI Mode)  ")
    print("==================================================\n")

    # 1. Candidate Workspace Selection
    candidates = get_all_candidates()
    candidate_id = None
    candidate_name = ""

    if candidates:
        print("Existing Candidate Profiles:")
        for idx, c in enumerate(candidates):
            print(f"[{idx + 1}] {c['name']}")
        print("[N] Create New Candidate Profile")
        
        choice = input("\nSelect candidate number or 'N': ").strip()
        if choice.upper() == 'N':
            candidate_name = input("Enter new candidate name: ").strip()
            candidate_id = create_candidate(candidate_name)
        else:
            try:
                selected_idx = int(choice) - 1
                candidate_id = candidates[selected_idx]['id']
                candidate_name = candidates[selected_idx]['name']
            except (ValueError, IndexError):
                print("Invalid choice. Creating temporary session.")
                candidate_name = "Guest Candidate"
                candidate_id = create_candidate(candidate_name)
    else:
        candidate_name = input("Enter candidate name: ").strip()
        candidate_id = create_candidate(candidate_name)

    # 2. Parse Ingestion File
    resume_path = input("\nEnter path to candidate resume (PDF, DOCX, or PNG/JPG): ").strip()
    if not os.path.exists(resume_path):
        print(f"Error: File '{resume_path}' does not exist.")
        return

    print("Parsing resume content...")
    raw_resume_text = ResumeParserTool.parse_file(resume_path)

    # 3. Collect Target Job Details
    print("\nSelect Job Input Method:")
    print("  [1] Job URL")
    print("  [2] Copy/Paste Job Description Text")
    method_choice = input("Choice (1/2): ").strip()

    is_url = (method_choice == "1")
    company_hint = ""

    if is_url:
        job_input = input("Paste Job URL: ").strip()
    else:
        print("Paste Job Description (press Enter twice to finish input):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        job_input = "\n".join(lines)
        company_hint = input("Company Name (optional, hit Enter to skip): ").strip()

    # 4. LLM Provider Configuration
    provider = input("\nSelect LLM Provider [openai/huggingface/ollama] (default: openai): ").strip().lower() or "openai"

    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ").strip()
    elif provider == "huggingface" and not os.environ.get("HUGGINGFACE_API_KEY"):
        os.environ["HUGGINGFACE_API_KEY"] = input("Enter Hugging Face Token: ").strip()

    if not os.environ.get("TAVILY_API_KEY"):
        os.environ["TAVILY_API_KEY"] = input("Enter Tavily API Key: ").strip()

    # 5. Kickoff Multi-Agent Process
    print("\n🚀 Executing multi-agent company research and resume tailoring...")
    crew = build_resume_tailor_crew(
        resume_text=raw_resume_text,
        job_input=job_input,
        is_url=is_url,
        company_name_hint=company_hint,
        provider=provider
    )

    result = crew.kickoff()
    markdown_output = str(result)

    # 6. Save Session to SQLite Database
    save_job_session(
        candidate_id=candidate_id,
        job_title="Target Role",
        company_name=company_hint or "Target Company",
        job_input=job_input,
        company_intel="CLI Processed",
        tailored_markdown=markdown_output
    )

    # 7. Generate Word and PDF Files
    formatted_name = candidate_name.replace(' ', '_')
    docx_path = f"Tailored_Resume_{formatted_name}.docx"
    pdf_path = f"Tailored_Resume_{formatted_name}.pdf"

    DocumentExporter.export_to_docx(markdown_output, docx_path)
    DocumentExporter.export_to_pdf(markdown_output, pdf_path)

    print("\n==================================================")
    print("  ✅ Process Complete!")
    print(f"  Word File Saved: {docx_path}")
    print(f"  PDF File Saved:  {pdf_path}")
    print("==================================================")

if __name__ == "__main__":
    run_cli()