import asyncio
import httpx
import time
import os
import sys
import json
import re
from dotenv import load_dotenv, find_dotenv
from groq import AsyncGroq
from pydantic import BaseModel

# Ensure UTF-8 output in Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env
load_dotenv(find_dotenv())

# 1. Pydantic Model (Day 3-4 concept: Structuring the LLM output)
class KeyInsights(BaseModel):
    title: str
    core_concept: str
    important_terms: list[str]

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

async def fetch_and_extract(url):
    slug = url.split('/')[-1]
    print(f"⏳ [{slug}] Web page fetch kar raha hu...")
    
    # 2. Async Web Request with User-Agent header (required by Wikipedia robot policy)
    headers = {"User-Agent": "ResearchBot/1.0 (student@example.com)"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as http_client:
        response = await http_client.get(url)
        response.raise_for_status()
        
        # Extract paragraph text from Wikipedia article
        paras = re.findall(r'<p\b[^>]*>(.*?)</p>', response.text, re.DOTALL)
        clean_paras = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()]
        text = ' '.join(clean_paras)[:2000]
        
    print(f"🧠 [{slug}] Data mil gaya. LLM se JSON extract karwa raha hu...")
    
    # LLM ko directly Pydantic ka schema dena taaki format fix rahe
    prompt = f"""
    Extract information from this text. 
    Return strictly in this JSON schema: {KeyInsights.model_json_schema()}
    
    Text: {text}
    """
    
    # 3. Async LLM Request (using supported Groq model)
    llm_response = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a data extraction agent. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"}, # Groq ko force karna ki JSON de
        temperature=0
    )
    
    print(f"✅ [{slug}] Extraction Done!")
    return json.loads(llm_response.choices[0].message.content)

async def main():
    urls = [
        "https://en.wikipedia.org/wiki/Agentic_AI",
        "https://en.wikipedia.org/wiki/Vector_database",
        "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"
    ]
    
    start_time = time.time()
    
    # 4. asyncio.gather (The Magic Sauce: Run everything simultaneously)
    tasks = [fetch_and_extract(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    print("\n" + "="*40)
    print("FINAL STRUCTURED DATA (Ready for Database or UI)")
    print("="*40)
    for res in results:
        print(json.dumps(res, indent=2))
        print("-" * 40)
        
    print(f"🚀 Total Time (3 Web Scrapes + 3 LLM Calls): {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())