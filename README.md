# CrewAI-Agent-Tailoring
# 📄 In-House AI Resume Tailoring & Corporate Intelligence System

An autonomous multi-agent resume tailoring workspace built with **Python**, **CrewAI**, and **Streamlit**. The system ingests candidate resumes (PDF, DOCX, or images via OCR), parses job postings (via URL scraping or pasted text), gathers corporate intelligence and growth projections, and rewrites resumes into ATS-optimized, ATS-compliant Word and PDF documents.

---

## ✨ Features

- **👥 Multi-Candidate Session Workspaces:** Manage isolated profiles (Person A, Person B, etc.) with persistent base resumes and session-based adaptation histories stored in a local SQLite database (`resumes.db`).
- **📥 Multimodal Ingestion Engine:** Extracts clean text from selectable PDFs (`PyMuPDF`), Word documents (`python-docx`), and scanned image/PDF files via Optical Character Recognition (`Tesseract OCR`).
- **🌐 Dynamic Job Description Handling:** Supports scraping live job posting URLs or processing pasted job description text.
- **🔍 Optional Web Search Intelligence:** Toggle **Tavily Web Search** on or off. When enabled, agents research corporate growth, financial health, and strategic priorities. When disabled, agents rely safely on internal LLM context.
- **🤖 Flexible LLM Provider Integration:** Switch seamlessly between:
  - **OpenAI:** `gpt-4o`
  - **Hugging Face Router (OpenAI-compatible):** `Qwen/Qwen2.5-72B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`
  - **Local Ollama:** `llama3.1`, `llama3.2`, `qwen2.5`
- **📑 ATS-Compliant Document Exporters:** Generates single-column, ATS-safe `.docx` and `.pdf` files devoid of tables, icons, multi-column layouts, or graphics that confuse ATS parsers.
- **🖥️ Dual Execution Modes:** Run via an interactive **Streamlit Web UI** (`app.py`) or a headless **Command-Line Interface** (`main.py`).

---

## 🏗️ Architecture & Multi-Agent Flow

```text
[Resume PDF / Image / Doc] ---> [1. Ingestion & OCR Engine]
                                        |
[Job URL or Pasted Text] ------> [2. Corporate Research Agent] (Optional Tavily Search)
                                        |
                                        v
                           [3. Skill & Gap Matcher Agent]
                                        |
                                        v
                           [4. ATS Content Writer Agent]
                                        |
                                        v
                           [5. DOCX & PDF Exporters]