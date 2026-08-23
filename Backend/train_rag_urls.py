import os
import json
import urllib.request
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

# Path to the RAG database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "my data", "knowledge_base.json")
# Fix path if script is run from inside Backend folder
if not os.path.exists(os.path.join(BASE_DIR, "..", "my data")):
    DB_PATH = os.path.join(BASE_DIR, "my data", "knowledge_base.json")

async def extract_agricultural_data(html_content, url):
    print("🤖 Extracting structured agricultural data using Gemini...")
    prompt = f"""
    You are an expert agricultural data extractor.
    Extract the crop, disease/pest, symptoms, and treatment options from the following webpage content.
    Return ONLY a valid JSON array of objects with this exact structure (no markdown, no backticks, just the raw JSON array):
    [
      {{
        "crop": "Name of crop",
        "disease": "Name of disease or pest",
        "symptoms": "Description of symptoms",
        "treatment_option_a": {{"name": "Chemical/Organic Name", "dosage": "Dosage info"}},
        "treatment_option_b": {{"name": "Alternative Name", "dosage": "Dosage info"}},
        "source": "{url}"
      }}
    ]
    
    Webpage Content (truncated):
    {html_content[:30000]}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }
    
    # Using Gemini 2.0 Flash for massive context and accuracy
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(api_url, json=payload)
        if resp.status_code == 200:
            raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = raw_text.strip()
            # Clean Markdown formatting if Gemini accidentally includes it
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            return json.loads(text)
        else:
            print(f"API Error: {resp.status_code} {resp.text}")
            return []

async def main():
    print("=========================================")
    print("🌱 KisanNet RAG URL Ingestion Tool")
    print("=========================================")
    print("Enter the URLs of agricultural university websites, government portals, or articles (one per line).")
    print("Enter 'done' when finished.")
    
    urls = []
    while True:
        url = input("URL: ").strip()
        if url.lower() == 'done':
            break
        if url:
            urls.append(url)
            
    if not urls:
        print("No URLs provided.")
        return

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Load existing DB
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            try:
                db_data = json.load(f)
            except:
                db_data = []
    else:
        db_data = []

    added_count = 0
    for url in urls:
        print(f"\n🌐 Fetching {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8', errors='ignore')
                extracted_list = await extract_agricultural_data(html, url)
                if extracted_list:
                    db_data.extend(extracted_list)
                    added_count += len(extracted_list)
                    print(f"✅ Added {len(extracted_list)} records from {url}")
                else:
                    print(f"⚠️ No records found or extracted for {url}")
        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")

    if added_count > 0:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=4, ensure_ascii=False)
        print(f"\n🎉 Successfully added {added_count} new records to your RAG knowledge base!")
        print(f"📊 Total records in RAG: {len(db_data)}")
        print("🎙️ The AI Voice Agent and Local RAG will now automatically use this new data.")
    else:
        print("\n⚠️ No new data was added.")

if __name__ == "__main__":
    asyncio.run(main())
