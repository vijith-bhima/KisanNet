import os
import re
import json
import httpx
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.trusted_sources import trusted_sources
from app.local_rag import local_rag

logger = logging.getLogger("agentic_research")

class AgenticResearchWorkflow:
    def __init__(self):
        # We use httpx directly for raw Gemini API calls as done in google_llm.py
        pass

    def _get_api_key(self) -> str:
        key = (
            os.getenv("GEMINI_API_KEY") or
            os.getenv("GOOGLE_API_KEY") or 
            getattr(settings, "GOOGLE_API_KEY", "")
        ).strip()
        return key

    async def _call_gemini_json(self, prompt: str) -> Dict[str, Any]:
        api_key = self._get_api_key()
        if not api_key:
            logger.error("No Gemini API key available for Agentic Research")
            return {}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1}
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:-3].strip()
                    elif raw_text.startswith("```"):
                        raw_text = raw_text[3:-3].strip()
                    return json.loads(raw_text)
                else:
                    logger.error(f"Gemini API error: {resp.status_code} - {resp.text}")
                    return {}
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return {}

    async def _call_gemini_text(self, prompt: str) -> str:
        api_key = self._get_api_key()
        if not api_key:
            return "Internal Error: Missing LLM API key."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    logger.error(f"Gemini API error: {resp.status_code}")
                    return "Internal Error: Could not generate response."
        except Exception as e:
            logger.error(f"Error calling Gemini Text: {e}")
            return "Internal Error: Could not generate response."

    async def analyze_intent(self, question: str) -> Dict[str, Any]:
        """Extracts farmer context and determines if web research is required."""
        logger.info(f"[AGENT] Analyzing intent for: {question}")
        prompt = f"""
        Analyze this farmer's question: "{question}"
        
        Extract agricultural context and decide research strategy.
        Return ONLY valid JSON with this exact structure:
        {{
            "crop": "Name of crop (or null)",
            "symptom": "Reported symptoms or disease (or null)",
            "requires_rag": true/false (true if general info/disease),
            "requires_web_research": true/false (true if requires specific dosage, exact govt scheme, or very recent data),
            "research_queries": ["query1", "query2"] (generate 2 effective search queries if web research is true. keep them short, e.g., 'chilli leaf curl disease treatment')
        }}
        """
        result = await self._call_gemini_json(prompt)
        logger.info(f"[AGENT] Intent detected: {result}")
        return result

    async def _duckduckgo_html_search(self, query: str, domains: List[str]) -> List[str]:
        """Scrape DuckDuckGo HTML Lite for search results (bypasses JS requirements)."""
        logger.info(f"[DDG] Searching for: {query}")
        
        # Clean domains of paths and preserve order, limit to 4
        clean_domains = []
        for d in domains:
            d_clean = d.split('/')[0]
            if d_clean not in clean_domains:
                clean_domains.append(d_clean)
        clean_domains = clean_domains[:15]
        
        site_filter = " OR ".join([f"site:{d}" for d in clean_domains])
        full_query = f"{query} {site_filter}"
        
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        logger.info(f"[RESEARCH] Searching trusted domains: {full_query}")
        links = []
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(url, data={"q": full_query}, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    # Simple regex to extract search result URLs
                    html = resp.text
                    matches = re.findall(r'href="//duckduckgo\.com/l/\?uddg=([^"&]+)', html)
                    import urllib.parse
                    for m in matches:
                        decoded_url = urllib.parse.unquote(m)
                        # Ensure it's actually from one of our trusted domains
                        if any(d in decoded_url for d in domains):
                            if decoded_url not in links:
                                links.append(decoded_url)
                            if len(links) >= 5: # Max 5 links per query
                                break
        except Exception as e:
            logger.error(f"[RESEARCH] Search failed: {e}")
            
        return links

    async def _fetch_and_extract_evidence(self, url: str) -> Dict[str, Any]:
        """Fetches webpage and returns raw text directly to save LLM processing time."""
        logger.info(f"[RESEARCH] Fetching URL: {url}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    import re
                    
                    def strip_html_tags(html_str):
                        # Fast HTML tag stripping in a background thread to prevent audio stuttering
                        c_text = re.sub(r'<[^>]+>', ' ', html_str)
                        return re.sub(r'\s+', ' ', c_text).strip()
                        
                    clean_text = await asyncio.to_thread(strip_html_tags, resp.text)
                    
                    return {
                        "found_evidence": True,
                        "evidence_summary": clean_text[:1500], # Pass 1500 chars of raw text directly to Voice LLM
                        "source_title": url
                    }
        except Exception as e:
            logger.error(f"[RESEARCH] Failed to extract {url}: {e}")
        return {}

    async def run_workflow(self, question: str, language: str = "Telugu") -> str:
        """Hyper-optimized orchestrator for voice agents."""
        try:
            # 1. Quickly translate to English for RAG and Web Search
            english_query = await self._call_gemini_text(
                f"Translate this farmer's question into a 2-4 word English search query. "
                f"Output ONLY the English keywords, nothing else. Question: {question}"
            )
            english_query = english_query.strip().replace('"', '').replace('\n', ' ')
            if not english_query or "Internal Error" in english_query:
                english_query = question
                
            # 2. Run RAG synchronously in a thread to not block asyncio
            def get_rag():
                return local_rag.search(english_query, top_k=2)
            rag_task = asyncio.to_thread(get_rag)
            
            # 3. Get domains and launch DDG search concurrently
            domains = trusted_sources.get_enabled_domains()
            
            ddg_task = self._duckduckgo_html_search(english_query, domains)
            
            rag_results, ddg_links = await asyncio.gather(rag_task, ddg_task, return_exceptions=True)
            
            rag_evidence = rag_results if isinstance(rag_results, list) else []
            urls_to_check = ddg_links if isinstance(ddg_links, list) else []
            urls_to_check = list(dict.fromkeys(urls_to_check))[:4]
            
            # 3. Content Extraction (Concurrent)
            web_evidence = []
            if urls_to_check:
                tasks = [self._fetch_and_extract_evidence(url) for url in urls_to_check]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                web_evidence = [r for r in results if isinstance(r, dict) and r.get("found_evidence")]
            
            if not rag_evidence and not web_evidence:
                return "NO DATA FOUND. Follow your system instructions for when no data is found."
            
            # 4. Return raw evidence to the Voice Agent directly
            rag_str = json.dumps(rag_evidence, ensure_ascii=False) if rag_evidence else "None"
            web_str = json.dumps(web_evidence, ensure_ascii=False) if web_evidence else "None"
            
            return f"EVIDENCE FOUND. RAG: {rag_str} | WEB: {web_str}. Follow your system instructions to explain this simply."
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"[AGENT] Workflow failed: {tb}")
            return "ERROR DURING SEARCH. Tell the user there was a technical error."

# Singleton instance
agentic_researcher = AgenticResearchWorkflow()
