import os
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool
from tavily import TavilyClient

class CompanyIntelligenceTools:

    @tool("Scrape Job Webpage")
    def scrape_job_url(url: str) -> str:
        """Extracts the main body text and job requirements from a job posting URL."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        return soup.get_text(separator="\n", strip=True)[:4000]

    @tool("Search Company Insights and Financials")
    def search_company_info(company_name: str) -> str:
        """Searches the web for recent news, revenue, growth, financial health, and strategic focus of a company."""
        tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
        query = f"{company_name} financial health growth strategy recent developments hiring news"
        response = tavily.search(query=query, search_depth="advanced", max_results=5)
        
        context = []
        for result in response.get("results", []):
            context.append(f"Title: {result['title']}\nContent: {result['content']}\n")
        return "\n---".join(context)