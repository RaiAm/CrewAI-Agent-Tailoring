# import os
# from dotenv import load_dotenv
# from crewai import LLM
# from crewai import Agent, Crew, Process, Task, LLM
# from tools.web_researcher import CompanyIntelligenceTools

# load_dotenv()

# local_llm = LLM(
#     model="ollama/llama3",
#     base_url="http://localhost:11434"
# )

# # Hugging Face Hosted Inference
# hf_llm = LLM(
#     model="huggingface/meta-llama/Meta-Llama-3-8B-Instruct",
#     api_key=os.getenv("huggingface_api_key")
# )/

import os
from crewai import Agent, Crew, Process, Task, LLM
from tools.web_researcher import CompanyIntelligenceTools

def build_resume_tailor_crew(resume_text: str, job_input: str, is_url: bool, company_name_hint: str = "", provider: str = "openai", custom_llm_model: str = "", use_tavily: bool = True):
    
    # Instantiate LLM dynamically inside the function call
    if provider == "huggingface":
        # Use Hugging Face's OpenAI-compatible Router endpoint
        hf_model = custom_llm_model or "Qwen/Qwen2.5-72B-Instruct"
        
        # Strip any redundant prefix if pasted by user
        if hf_model.startswith("huggingface/"):
            hf_model = hf_model.replace("huggingface/", "")

        llm_engine = LLM(
            model=f"openai/{hf_model}",
            base_url="https://router.huggingface.co/v1",
            api_key=os.environ.get("huggingface_api_key")
        )
    elif provider == "ollama":
        llm_engine = LLM(
            model=custom_llm_model or "ollama/llama3",
            base_url="http://localhost:11434"
        )
    else:
        llm_engine = LLM(
            model="gpt-4o",
            api_key=os.environ.get("OPENAI_API_KEY")
        )

    research_tools = []
    if is_url:
        research_tools.append(CompanyIntelligenceTools.scrape_job_url)
    
    # Only attach web search tool if Tavily is enabled by user
    if use_tavily and os.environ.get("TAVILY_API_KEY"):
        research_tools.append(CompanyIntelligenceTools.search_company_info)

    # 1. Company & Job Intelligence Researcher
    researcher = Agent(
        role="Corporate Intelligence Researcher",
        goal="Extract job specifications and research target company financial status, growth trajectory, and current works.",
        backstory="An expert corporate analyst proficient in extracting strategic hiring context and company performance indicators.",
        tools=research_tools,
        llm=llm_engine,
        verbose=True
    )

    # 2. Candidate Context & Gap Analyst
    gap_analyst = Agent(
        role="Talent Acquisition & Skill Matcher",
        goal="Extract candidate background and cross-reference skills against job requirements and company strategic goals.",
        backstory="A seasoned headhunter who identifies transferable skills, missing keywords, and experience gaps.",
        llm=llm_engine,
        verbose=True
    )

    # 3. ATS Resume Writer
    writer = Agent(
        role="ATS Optimization Specialist",
        goal="Rewrite and optimize resume bullet points using the STAR method while embedding high-value target keywords without hallucinating facts.",
        backstory="An expert resume writer trained on Enterprise Applicant Tracking Systems (ATS) and hiring algorithms.",
        llm=llm_engine,
        verbose=True
    )

    # Prepare input description based on URL or Text input
    if is_url:
        input_instruction = f"Scrape the job posting URL: {job_input}. Extract the company name, job title, and core requirements."
    else:
        input_instruction = f"Analyze the following job description text:\n\n{job_input}\n\nExtract the core requirements, key responsibilities, and identify the company name."

    if company_name_hint:
        input_instruction += f"\nNote: The user specified the company name is '{company_name_hint}'."

    t1_research = Task(
        description=f"{input_instruction}\n\nOnce the company name is identified, use the 'Search Company Insights and Financials' tool to retrieve recent growth, financial status, revenue estimates, and recent company projects.",
        expected_output="A structured report containing Job Requirements, Key Skills, and Company Intelligence (growth, budget, recent projects).",
        agent=researcher
    )

    t2_analysis = Task(
        description=f"Analyze candidate's raw resume:\n\n{resume_text}\n\nCompare it against the research output from Task 1. Identify key missing ATS keywords, top transferable achievements, and alignment points.",
        expected_output="A detailed gap analysis highlighting matched skills, missing keywords, and strategic framing angles.",
        agent=gap_analyst
    )

    t3_write_resume = Task(
        description="Rewrite the candidate's resume in Markdown format. Follow these rules:\n"
                   "1. Use standard headers: Summary, Technical Skills, Professional Experience, Projects, Education.\n"
                   "2. Frame experience bullets around the company's strategic goals and job requirements using action verbs + metrics.\n"
                   "3. NEVER fabricate companies, dates, or non-existent degrees/skills.\n"
                   "4. Ensure 100% ATS readability.",
        expected_output="A full, ATS-optimized resume formatted cleanly in Markdown.",
        agent=writer
    )

    return Crew(
        agents=[researcher, gap_analyst, writer],
        tasks=[t1_research, t2_analysis, t3_write_resume],
        process=Process.sequential,
        verbose=True
    )

# def build_resume_tailor_crew(resume_text: str, job_input: str, is_url: bool, company_name_hint: str = "", provider: str = "openai", custom_llm_model: str = ""):
    
#     # Configure LLM Provider (Supports OpenAI, Hugging Face, or Ollama)
#     if provider == "huggingface":
#         llm_engine = LLM(model=custom_llm_model or "huggingface/meta-llama/Meta-Llama-3-8B-Instruct", api_key=os.environ.get("HUGGINGFACE_API_KEY"))
#     elif provider == "ollama":
#         llm_engine = LLM(model=custom_llm_model or "ollama/llama3", base_url="http://localhost:11434")
#     else:
#         llm_engine = LLM(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY"))

#     researcher = Agent(
#         role="Corporate Intelligence Researcher",
#         goal="Extract job specifications and research target company financial status, growth trajectory, and current works.",
#         backstory="An expert corporate analyst proficient in extracting strategic hiring context and company performance indicators.",
#         tools=[CompanyIntelligenceTools.scrape_job_url, CompanyIntelligenceTools.search_company_info],
#         llm=llm_engine,
#         verbose=True
#     )

#     gap_analyst = Agent(
#         role="Talent Acquisition & Skill Matcher",
#         goal="Extract candidate background and cross-reference skills against job requirements and company strategic goals.",
#         backstory="A seasoned headhunter who identifies transferable skills, missing keywords, and experience gaps.",
#         llm=llm_engine,
#         verbose=True
#     )

#     writer = Agent(
#         role="ATS Optimization Specialist",
#         goal="Rewrite and optimize resume bullet points using the STAR method while embedding high-value target keywords without hallucinating facts.",
#         backstory="An expert resume writer trained on Enterprise Applicant Tracking Systems (ATS) and hiring algorithms.",
#         llm=llm_engine,
#         verbose=True
#     )

#     if is_url:
#         input_instruction = f"Scrape the job posting URL: {job_input}. Extract the company name, job title, and core requirements."
#     else:
#         input_instruction = f"Analyze the following job description text:\n\n{job_input}\n\nExtract the core requirements, key responsibilities, and identify the company name."

#     if company_name_hint:
#         input_instruction += f"\nNote: The user specified the company name is '{company_name_hint}'."

#     t1_research = Task(
#         description=f"{input_instruction}\n\nOnce the company name is identified, use the 'Search Company Insights and Financials' tool to retrieve recent growth, financial status, revenue estimates, and recent company projects.",
#         expected_output="A structured report containing Job Requirements, Key Skills, and Company Intelligence (growth, budget, recent projects).",
#         agent=researcher
#     )

#     t2_analysis = Task(
#         description=f"Analyze candidate's raw resume:\n\n{resume_text}\n\nCompare it against the research output from Task 1. Identify key missing ATS keywords, top transferable achievements, and alignment points.",
#         expected_output="A detailed gap analysis highlighting matched skills, missing keywords, and strategic framing angles.",
#         agent=gap_analyst
#     )

#     t3_write_resume = Task(
#         description="Rewrite the candidate's resume in Markdown format. Follow these rules:\n"
#                    "1. Use standard headers: Summary, Technical Skills, Professional Experience, Projects, Education.\n"
#                    "2. Frame experience bullets around the company's strategic goals and job requirements using action verbs + metrics.\n"
#                    "3. NEVER fabricate companies, dates, or non-existent degrees/skills.\n"
#                    "4. Ensure 100% ATS readability.",
#         expected_output="A full, ATS-optimized resume formatted cleanly in Markdown.",
#         agent=writer
#     )

#     return Crew(
#         agents=[researcher, gap_analyst, writer],
#         tasks=[t1_research, t2_analysis, t3_write_resume],
#         process=Process.sequential,
#         verbose=True
#     )