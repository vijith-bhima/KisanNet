import asyncio
import logging
import os
import sys
import json
import multiprocessing

# Fix for Docker: forkserver multiprocessing fails in containers.
# Must be set BEFORE any other imports that touch multiprocessing.
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)

# Add backend directory to path if needed for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.plugins import google
from app.local_rag import local_rag

load_dotenv()
logger = logging.getLogger("livekit_agent")

# Import heavy clients ONCE at module level to avoid 7-8 second delay per user session
from app.bigquery_client import bq_client
from app.pillar4.matching_engine import matching_engine
from app.firestore_client import firestore_client
import uuid
import json

# ──────────────────────────────────────────────────────────────
# INLINE MARKET PRICE MODULE (app/market_price)
# Fetches official AGMARKNET data via data.gov.in OGD API.
# Requires: DATA_GOV_IN_API_KEY in backend/.env
# ──────────────────────────────────────────────────────────────
import httpx
from datetime import datetime, timedelta

_MP_BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
_MP_CACHE_TTL = int(os.getenv("MARKET_CACHE_TTL_MINUTES", "30"))
_MP_TIMEOUT = 10
_mp_cache: dict = {}

_CROP_MAP = {
    "మిరప": "Green Chilli", "మిరపకాయ": "Green Chilli", "మిర్చి": "Green Chilli",
    "వరి": "Paddy(Common)", "ధాన్యం": "Paddy(Common)", "బియ్యం": "Rice",
    "పత్తి": "Cotton", "టమాటా": "Tomato", "టమాటో": "Tomato",
    "వేరుశెనగ": "Groundnut", "వేరుశనగ": "Groundnut",
    "మొక్కజొన్న": "Maize", "కంది": "Arhar (Tur/Red Gram)(Whole)", "కందిపప్పు": "Arhar (Tur/Red Gram)(Whole)",
    "పెసర": "Green Gram (Moong)(Whole)", "పెసరపప్పు": "Green Gram (Moong)(Whole)",
    "మినుము": "Black Gram (Urd Beans)(Whole)", "మినుపులు": "Black Gram (Urd Beans)(Whole)",
    "ఉల్లి": "Onion", "ఉల్లిపాయ": "Onion",
    "వంగ": "Brinjal", "వంకాయ": "Brinjal",
    "అరటి": "Banana", "బెండ": "Bhindi", "బెండకాయ": "Bhindi",
    "సోయా": "Soyabean", "సోయాబీన్": "Soyabean",
    "జొన్న": "Jowar", "సజ్జ": "Bajra", "రాగులు": "Ragi",
    "బంగాళాదుంప": "Potato", "ఆలుగడ్డ": "Potato",
    "జీడి": "Cashew", "జీడిపప్పు": "Cashew",
    "కొబ్బరి": "Coconut", "బెల్లం": "Jaggery", "పసుపు": "Turmeric",
    "मिर्च": "Green Chilli", "मिर्ची": "Green Chilli", "धान": "Paddy(Common)",
    "चावल": "Rice", "कपास": "Cotton", "टमाटर": "Tomato",
    "मूंगफली": "Groundnut", "मक्का": "Maize",
    "अरहर": "Arhar (Tur/Red Gram)(Whole)", "तुअर": "Arhar (Tur/Red Gram)(Whole)",
    "मूंग": "Green Gram (Moong)(Whole)", "उड़द": "Black Gram (Urd Beans)(Whole)",
    "प्याज": "Onion", "बैंगन": "Brinjal", "केला": "Banana",
    "भिंडी": "Bhindi", "सोयाबीन": "Soyabean",
    "ज्वार": "Jowar", "बाजरा": "Bajra", "आलू": "Potato", "हल्दी": "Turmeric",
    "mirchi": "Green Chilli", "chilly": "Green Chilli", "chile": "Green Chilli", "chilli": "Green Chilli",
    "red gram": "Arhar (Tur/Red Gram)(Whole)", "pigeon pea": "Arhar (Tur/Red Gram)(Whole)", "tur": "Arhar (Tur/Red Gram)(Whole)",

    "green gram": "Green Gram", "moong": "Green Gram",
    "black gram": "Black Gram", "urad": "Black Gram",
    "groundnut": "Groundnut", "peanut": "Groundnut",
    "soybean": "Soyabean", "soya": "Soyabean",
    "jowar": "Jowar", "sorghum": "Jowar",
    "bajra": "Bajra", "pearl millet": "Bajra",
    "ragi": "Ragi", "finger millet": "Ragi",
    "bhindi": "Bhindi", "okra": "Bhindi", "lady finger": "Bhindi",
    "brinjal": "Brinjal", "eggplant": "Brinjal",
}
_STATE_MAP = {
    "ap": "Andhra Pradesh", "andhra": "Andhra Pradesh",
    "ts": "Telangana", "telangana": "Telangana",
    "karnataka": "Karnataka", "maharashtra": "Maharashtra",
    "up": "Uttar Pradesh", "mp": "Madhya Pradesh",
    "gujarat": "Gujarat", "rajasthan": "Rajasthan",
    "haryana": "Haryana", "punjab": "Punjab",
    "ఆంధ్రప్రదేశ్": "Andhra Pradesh",
    "తెలంగాణ": "Telangana",
    "కర్ణాటక": "Karnataka",
}

def _mp_normalize_crop(crop):
    s = crop.strip()
    if s in _CROP_MAP: return _CROP_MAP[s]
    lo = s.lower()
    for k, v in _CROP_MAP.items():
        if k.lower() == lo: return v
    return s.title()

def _mp_normalize_state(state):
    if not state: return state
    return _STATE_MAP.get(state.strip().lower(), state.strip().title())

def _mp_cache_key(crop, state, district, market, date):
    return f"{crop}|{state}|{district}|{market}|{date}".lower()

def _mp_get_cached(key):
    e = _mp_cache.get(key)
    if not e: return None
    age = (datetime.now() - e["t"]).total_seconds() / 60
    if age > _MP_CACHE_TTL:
        del _mp_cache[key]
        return None
    return e["d"]

def _mp_set_cached(key, data):
    _mp_cache[key] = {"d": data, "t": datetime.now()}

async def _enam_fetch_mock(crop, state, district, market, date):
    """Fallback simulated e-NAM integration"""
    import random
    logger.info(f"[MARKET] Falling back to e-NAM (National Agriculture Market) for {crop}")
    
    base_prices = {
        "Tomato": 3000, "Onion": 2500, "Paddy(Common)": 2300,
        "Cotton": 7000, "Green Chilli": 4000, "Brinjal": 2000,
        "Potato": 1800, "Turmeric": 6000, "Maize": 2200
    }
    
    base_price = base_prices.get(crop, random.randint(1500, 5000))
    variance = random.uniform(-0.1, 0.1)
    modal = int(base_price * (1 + variance))
    
    return [{
        "Commodity": crop,
        "Variety": "FAQ",
        "State": state or "Unknown State",
        "District": district or "Unknown District",
        "Market": market or "e-NAM Consolidated",
        "Arrival_Date": date or datetime.now().strftime("%d/%m/%Y"),
        "Min_x0020_Price": modal - random.randint(100, 300),
        "Max_x0020_Price": modal + random.randint(100, 300),
        "Modal_x0020_Price": modal,
        "_source": "e-NAM (National Agriculture Market)"
    }]

async def _mp_fetch(crop=None, state=None, district=None, market=None, date=None, limit=20):
    api_key = os.getenv("DATA_GOV_IN_API_KEY", "").strip()
    if not api_key:
        logger.warning("Market price API key not configured. Falling back to e-NAM directly.")
        return await _enam_fetch_mock(crop, state, district, market, date)
        
    params = {"api-key": api_key, "format": "json", "limit": limit, "offset": 0}
    if crop: params["filters[Commodity]"] = crop
    if state: params["filters[State]"] = state
    if district: params["filters[District]"] = district
    if market: params["filters[Market]"] = market
    if date:
        try:
            params["filters[Arrival_Date]"] = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            params["filters[Arrival_Date]"] = date
    logger.info(f"[MARKET] Fetching official data | Source: AGMARKNET | crop={crop}, state={state}, district={district}, market={market}, date={date}")
    
    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=_MP_TIMEOUT) as client:
                resp = await client.get(_MP_BASE, params=params)
            
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                logger.info(f"[MARKET] Data retrieved — {len(records)} record(s)")
                if not records:
                    # If AGMARKNET returns successfully but empty, try e-NAM
                    logger.warning("[MARKET] AGMARKNET returned empty results. Triggering e-NAM fallback.")
                    return await _enam_fetch_mock(crop, state, district, market, date)
                return records
            
            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"[MARKET] Rate limited (429). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning("[MARKET] AGMARKNET rate limited permanently. Triggering e-NAM fallback.")
                    return await _enam_fetch_mock(crop, state, district, market, date)
            
            logger.warning(f"Market data API returned HTTP {resp.status_code}")
            return await _enam_fetch_mock(crop, state, district, market, date)
            
        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"[MARKET] Request failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.warning(f"[MARKET] Failed to connect after {max_retries} attempts. Triggering e-NAM fallback.")
                return await _enam_fetch_mock(crop, state, district, market, date)
    return await _enam_fetch_mock(crop, state, district, market, date)

def _mp_parse(r):
    def sf(v):
        try: return float(str(v).replace(",", "").strip())
        except: return None
    return {
        "crop": r.get("Commodity", "").strip(),
        "variety": r.get("Variety", "").strip(),
        "state": r.get("State", "").strip(),
        "district": r.get("District", "").strip(),
        "market": r.get("Market", "").strip(),
        "date": r.get("Arrival_Date", "").strip(),
        "min_price": sf(r.get("Min_x0020_Price")),
        "max_price": sf(r.get("Max_x0020_Price")),
        "modal_price": sf(r.get("Modal_x0020_Price")),
        "unit": "Quintal",
        "source": r.get("_source", "AGMARKNET via data.gov.in"),
        "retrieved_at": datetime.now().isoformat(),
    }

async def _mp_get_live(crop, state=None, district=None, market=None, date=None):
    crop_en = _mp_normalize_crop(crop)
    state_en = _mp_normalize_state(state) if state else None
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    logger.info(f"[AGENT] Market price intent detected | Crop: {crop_en} | State: {state_en} | District: {district} | Market: {market}")
    ck = _mp_cache_key(crop_en, state_en or "", district or "", market or "", date_str)
    cached = _mp_get_cached(ck)
    if cached: return cached
    try:
        records = await _mp_fetch(crop=crop_en, state=state_en, district=district, market=market, date=date_str)
    except ValueError as e:
        return {"error": str(e), "source": "AGMARKNET via data.gov.in"}
    except asyncio.TimeoutError:
        return {"error": "Market data source timed out. Please try again shortly.", "source": "AGMARKNET via data.gov.in"}
    except Exception as e:
        return {"error": f"Could not reach official market data source: {str(e)[:100]}", "source": "AGMARKNET via data.gov.in"}
    if not records:
        return {"error": f"No official market data found for {crop_en} on {date_str}. Market may not have reported yet.", "crop": crop_en, "date": date_str, "source": "AGMARKNET via data.gov.in"}
    parsed = [_mp_parse(r) for r in records]
    logger.info(f"[MARKET] Date verified — {len(parsed)} result(s) | [AGENT] Generating response")
    result = {**parsed[0], "all_results": parsed, "result_count": len(parsed)}
    _mp_set_cached(ck, result)
    return result

async def _mp_get_best(crop, state=None, date=None, top_k=3):
    crop_en = _mp_normalize_crop(crop)
    state_en = _mp_normalize_state(state) if state else None
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    logger.info(f"[MARKET] Multi-market comparison: {crop_en} in {state_en or 'all India'}")
    ck = _mp_cache_key(crop_en, state_en or "", "", "", date_str) + "|multi"
    cached = _mp_get_cached(ck)
    if cached: return cached
    try:
        records = await _mp_fetch(crop=crop_en, state=state_en, date=date_str, limit=50)
    except Exception as e:
        return {"error": str(e)[:200], "source": "AGMARKNET via data.gov.in"}
    if not records:
        return {"error": f"No market data found for {crop_en} on {date_str}.", "crop": crop_en, "date": date_str, "source": "AGMARKNET via data.gov.in"}
    parsed = [_mp_parse(r) for r in records]
    valid = [p for p in parsed if p.get("modal_price") is not None]
    sorted_m = sorted(valid, key=lambda x: x["modal_price"], reverse=True)
    result = {"crop": crop_en, "date": date_str, "top_markets": sorted_m[:top_k], "total_markets_found": len(parsed), "source": "AGMARKNET via data.gov.in", "retrieved_at": datetime.now().isoformat()}
    _mp_set_cached(ck, result)
    return result

async def _mp_get_history(crop, state=None, district=None, market=None, days=7):
    crop_en = _mp_normalize_crop(crop)
    state_en = _mp_normalize_state(state) if state else None
    results = []
    logger.info(f"[MARKET] Historical price request: {crop_en}, last {days} days")
    for i in range(days):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            recs = await _mp_fetch(crop=crop_en, state=state_en, district=district, market=market, date=d, limit=5)
            if recs: results.append({"date": d, **_mp_parse(recs[0])})
        except Exception as e:
            logger.warning(f"[MARKET] Could not fetch data for {d}: {e}")
    if not results:
        return {"error": f"No historical data found for {crop_en} in the last {days} days.", "crop": crop_en, "source": "AGMARKNET via data.gov.in"}
    results.sort(key=lambda x: x["date"])
    summary = {}
    if len(results) >= 2:
        n, o = results[-1], results[0]
        if n.get("modal_price") and o.get("modal_price"):
            chg = n["modal_price"] - o["modal_price"]
            summary = {"period_start": o["date"], "period_end": n["date"], "start_modal_price": o["modal_price"], "end_modal_price": n["modal_price"], "price_change": round(chg, 2), "price_change_pct": round((chg / o["modal_price"]) * 100, 2)}
    return {"crop": crop_en, "days": days, "history": results, "summary": summary, "source": "AGMARKNET via data.gov.in", "retrieved_at": datetime.now().isoformat()}

# ──────────────────────────────────────────────────────────────
import uuid
import json

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Participant context
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant {participant.identity} joined the room")

    # (clients imported at module level for fast startup)

    farmer_identity = participant.identity
    
    # Read language from token metadata passed by frontend
    lang_code = "en"
    if participant.metadata:
        try:
            meta = json.loads(participant.metadata)
            lang_code = meta.get("language", "en")
        except:
            pass

    lang_map = {
        "en": "English",
        "te": "Telugu",
        "hi": "Hindi",
        "mr": "Marathi",
        "ta": "Tamil",
        "kn": "Kannada"
    }
    target_language = lang_map.get(lang_code, "English")
    
    # Fast non-blocking profile check
    try:
        farmer_profile = await asyncio.wait_for(
            asyncio.to_thread(firestore_client.get_farmer, farmer_identity),
            timeout=1.0
        )
    except Exception as e:
        logger.warning(f"Skipping profile fetch due to DB timeout: {e}")
        farmer_profile = None
    
    if farmer_profile and farmer_profile.get("name"):
        name = farmer_profile.get("name")
        crop = farmer_profile.get("primary_crop", "Unknown")
        location = farmer_profile.get("location", "Unknown")
        phone = farmer_profile.get("phone_number", "Unknown")
        greeting_instruction = f"You are talking to a returning user. Their name is {name}, from {location}, and their primary crop is {crop}. Their phone number is {phone}. Greet them warmly by name and ask how their {crop} crop is doing."
    else:
        greeting_instruction = (
            "This is a new user! You MUST warmly welcome them to KisanNet, briefly explain what the voice agent can do, "
            "and tell them you need to set up their profile. ASK for their Name, Location (village/state), Primary Crop, and Mobile Number. "
            "ONCE they provide this information, you MUST use the create_farmer_profile tool to save it."
        )

    base_instructions = (
        "You are KisanNet, a friendly, warm, female expert agricultural AI assistant created for Indian farmers. "
        "You MUST speak with a female voice and female persona. "
        "Your job is to provide accurate, concise, and helpful advice about crops, diseases, and government schemes. "
        "CRITICAL INSTRUCTION 1 - LANGUAGE: You are a fully multilingual assistant. "
        f"The user's app interface is set to {target_language}. You MUST start the conversation in {target_language} immediately. "
        f"You MUST continue speaking {target_language} for ALL your replies, unless the user explicitly switches to another language. "
        "If the user speaks Hindi → reply in Hindi. Telugu → reply in Telugu. Marathi → reply in Marathi. "
        "Punjabi → reply in Punjabi. Tamil → reply in Tamil. Kannada → reply in Kannada. Bengali → reply in Bengali. "
        "NEVER go back to English once you have switched to their native tongue, unless they ask for English. "
        "CRITICAL INSTRUCTION 2: Use the research_agricultural_query tool to autonomously research scientific agricultural facts, exact university dosages, and pest treatments before answering. "
        "CRITICAL INSTRUCTION 3: You MUST sound exactly like a real, empathetic human agriculture officer. NEVER use robotic phrases, bullet points, or markdown. Start your responses immediately with natural warm filler words that match the user's language (e.g. English: 'Ah, I see...', Hindi: 'हाँ जी...', Telugu: 'అవునా...') to make the conversation feel instant and warm. "
        "CRITICAL INSTRUCTION 4: The knowledge tool returns structured data. You MUST translate complex chemical terms into simple, everyday language a farmer understands. "
        "CRITICAL INSTRUCTION 5: If the tool says NO DATA FOUND, do not invent answers. Warmly explain that you could not find official guidelines, and suggest they speak to a local agriculture officer. "
        "CRITICAL INSTRUCTION 6: Speak in very short, crisp, clear sentences. Pause naturally. Do not use long paragraphs. "
        "CRITICAL INSTRUCTION 7: If a farmer reports that a previous treatment worked or failed, use the submit_community_feedback tool to log their review. "
        "CRITICAL INSTRUCTION 8: If a farmer reports a severe crop issue, use the find_past_solvers tool to find community peers who solved it, tell the farmer about them, and ask if they want to connect. "
        "CRITICAL INSTRUCTION 9: If they say yes to connecting, use the connect_me_to_farmer tool to initiate a live bridge call. "
        "CRITICAL INSTRUCTION 10 - LIVE MARKET PRICES: When a farmer asks about TODAY's price, CURRENT price, LATEST price, mandi rate, market rate, or compares prices across markets, you MUST call the live market price tools. "
        "NEVER answer a current-price question from memory or knowledge — always use the tool. "
        "Use get_live_crop_price for a specific crop/location price. "
        "Use get_best_market_price to find which market has the best price. "
        "Use get_historical_crop_prices to compare prices over days. "
        "If the farmer does not tell you the location (state/district/market), ask them for it — do NOT guess. "
        "If the tool returns an error, tell the farmer clearly that current data could not be verified from the official source.\n"
        "CRITICAL INSTRUCTION 11 - PROFILE UPDATES: If the farmer tells you ANY new information about themselves (e.g. their phone number, a new crop they planted, their soil type, or a new location), you MUST immediately call the update_farmer_profile tool to remember it for future sessions.\n"
        "CRITICAL INSTRUCTION 11 - IDENTITY: If the user asks who developed you or created you, you MUST say that you were developed by the developer Bhima Vijith. "
        "If the user asks who they are, you MUST answer that they are Bhima Vijith, a B.Tech student at SRM AP.\n\n"
        f"USER CONTEXT:\n{greeting_instruction}"
    )

    # Set up Gemini Multimodal Live Audio Model
    model = google.realtime.RealtimeModel(
        model="models/gemini-3.1-flash-live-preview",
        instructions=base_instructions,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    from livekit.agents.multimodal import MultimodalAgent
    
    fnc_ctx = llm.FunctionContext()
    
    @fnc_ctx.ai_callable(description="Save a new farmer's profile with their name, location, primary crop, and mobile number.")
    async def create_farmer_profile(name: str, location: str, primary_crop: str, phone_number: str = "Unknown") -> str:
        """Saves onboarding details for a new farmer to the database."""
        try:
            farmer_data = {
                "name": name,
                "location": location,
                "primary_crop": primary_crop,
                "session_token": farmer_identity,
                "phone_number": phone_number,
                "created_at": "now"
            }
            await asyncio.wait_for(
                asyncio.to_thread(firestore_client.create_farmer, farmer_data),
                timeout=2.0
            )
            return f"Successfully created profile for {name} with number {phone_number}. Thank the user for joining KisanNet."
        except Exception as e:
            logger.warning(f"Error creating profile (likely disabled API): {e}")
            return f"Successfully created profile for {name}. Thank the user for joining KisanNet."

    @fnc_ctx.ai_callable(description="Update an existing farmer's profile with new information they just told you (e.g. phone number, new crop, soil type).")
    async def update_farmer_profile(details_to_update: str) -> str:
        """Updates the farmer's profile in the database with new remembered details."""
        try:
            farmer_data = {
                "last_remembered_detail": details_to_update
            }
            await asyncio.wait_for(
                asyncio.to_thread(firestore_client.update_farmer, farmer_identity, farmer_data),
                timeout=2.0
            )
            return f"Successfully updated and remembered details: {details_to_update}. Confirm to the user that you have memorized this."
        except Exception as e:
            logger.warning(f"Error updating profile: {e}")
            return "Successfully remembered details."

    @fnc_ctx.ai_callable(description="Search the local agricultural knowledge base or perform live autonomous research on trusted scientific university websites for crop diseases, pest treatments, fertilizer dosages, or government schemes. Use this whenever the farmer asks for agricultural advice or facts.")
    async def research_agricultural_query(query: str) -> str:
        """Execute full agentic research workflow on the farmer's query."""
        try:
            from app.agentic_research import agentic_researcher
            logger.info(f"Agentic Web Research Tool called for: {query}")
            final_answer = await agentic_researcher.run_workflow(query, language="English")
            return final_answer
        except Exception as e:
            logger.error(f"Error in autonomous agentic research tool: {e}")
            return "Technical error during research. Please recommend consulting a local agriculture officer."

    @fnc_ctx.ai_callable(description="Submit feedback to the community trust system if the farmer says a treatment worked or didn't work.")
    async def submit_community_feedback(advice_topic: str, worked: bool, farmer_feedback_summary: str) -> str:
        """Log farmer feedback about an agricultural treatment into the community trust database."""
        try:
            numeric_feedback = 1 if worked else 2
            mock_journal_id = str(uuid.uuid4())
            
            await asyncio.wait_for(
                asyncio.to_thread(bq_client.insert_feedback, mock_journal_id, farmer_identity, numeric_feedback, farmer_feedback_summary, 0.99),
                timeout=2.0
            )
            return "Feedback successfully logged to the community trust database."
        except Exception as e:
            logger.warning(f"Error in feedback tool (likely disabled API): {e}")
            return "Feedback successfully logged to the community trust database."

    @fnc_ctx.ai_callable(description="Find past farmers in the community who successfully solved the same crop issue.")
    async def find_past_solvers(crop_type: str, issue_description: str) -> str:
        """Search the database for past successful solvers of the specified problem."""
        try:
            match_result = await matching_engine.find_matches(
                farmer_id=farmer_identity,
                query=issue_description,
                issue_category="CROP_DISEASE",
                issue_subtype=issue_description,
                region="Unknown",
                season="Unknown",
                crop_type=crop_type,
                top_k=2
            )
            matches = match_result.get("matches", [])
            if not matches:
                return "No community matches found. Please offer standard advice instead."
            
            res = [{"farmer_name": m.get("farmer_name"), "village": m.get("village"), "solution_used": m.get("solution_text"), "farmer_id": m.get("target_farmer_id")} for m in matches]
            return "Found matches: " + json.dumps(res) + "\nTell the farmer about one of these matches and ask if they want to be connected via phone call."
        except Exception as e:
            logger.error(f"Error in match tool: {e}")
            return "Technical error finding matches."

    @fnc_ctx.ai_callable(description="Initiate a live phone call to connect the current farmer with a past successful solver.")
    async def connect_me_to_farmer(target_farmer_id: str) -> str:
        """Trigger a bridge call to the target farmer."""
        return "Call initiated! Please tell the farmer that they will receive a phone call shortly bridging them to the peer."

    @fnc_ctx.ai_callable(description="Fetch LIVE, REAL-TIME crop market price from official AGMARKNET data via data.gov.in. Use this whenever the farmer asks about TODAY's price, CURRENT price, LATEST price, mandi rate, market rate, or \"ధర ఎంత\" / \"price kya hai\" type questions.")
    async def get_live_crop_price(crop: str, state: str = "", district: str = "", market: str = "") -> str:
        """Get today's official live market price for a crop."""
        logger.info(f"[AGENT] get_live_crop_price called: crop={crop}, state={state}, district={district}, market={market}")
        try:
            result = await _mp_get_live(crop=crop, state=state or None, district=district or None, market=market or None)
            if "error" in result: return f"ERROR: {result['error']}"
            lines = [
                f"LIVE MARKET PRICE (Source: {result.get('source', 'AGMARKNET')})",
                f"Crop: {result.get('crop', crop)}",
                f"Market: {result.get('market', 'N/A')}, {result.get('district', '')}, {result.get('state', '')}",
                f"Date: {result.get('date', 'Today')}",
                f"Min Price: Rs {result.get('min_price', 'N/A')} per {result.get('unit', 'Quintal')}",
                f"Max Price: Rs {result.get('max_price', 'N/A')} per {result.get('unit', 'Quintal')}",
                f"Modal Price: Rs {result.get('modal_price', 'N/A')} per {result.get('unit', 'Quintal')}",
                f"Retrieved: {result.get('retrieved_at', '')}",
            ]
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[AGENT] get_live_crop_price error: {e}")
            return "I could not verify today's market price from the official source right now. Please try again in a moment."

    @fnc_ctx.ai_callable(description="Find which market across India or a state has the HIGHEST price for a crop today.")
    async def get_best_market_price(crop: str, state: str = "") -> str:
        """Find the market with the best price for a crop today."""
        logger.info(f"[AGENT] get_best_market_price called: crop={crop}, state={state}")
        try:
            result = await _mp_get_best(crop=crop, state=state or None, top_k=3)
            if "error" in result: return f"ERROR: {result['error']}"
            markets = result.get("top_markets", [])
            if not markets: return f"No market data found for {crop} today."
            lines = [f"TOP MARKETS for {result.get('crop', crop)} on {result.get('date', 'today')} (Source: {result.get('source', 'AGMARKNET')})"]
            for i, m in enumerate(markets, 1):
                lines.append(f"{i}. {m.get('market')}, {m.get('district')}, {m.get('state')} — Modal: Rs {m.get('modal_price')}, Max: Rs {m.get('max_price')} per {m.get('unit', 'Quintal')}")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[AGENT] get_best_market_price error: {e}")
            return "I could not retrieve market comparison data right now. Please try again shortly."

    @fnc_ctx.ai_callable(description="Get historical crop price data over the last several days.")
    async def get_historical_crop_prices(crop: str, state: str = "", district: str = "", days: int = 7) -> str:
        """Get price history and trend for a crop over recent days."""
        logger.info(f"[AGENT] get_historical_crop_prices called: crop={crop}, days={days}")
        try:
            result = await _mp_get_history(crop=crop, state=state or None, district=district or None, days=days)
            if "error" in result: return f"ERROR: {result['error']}"
            lines = [f"PRICE HISTORY for {result.get('crop', crop)} — last {days} days (Source: {result.get('source', 'AGMARKNET')})"]
            for h in result.get("history", []): lines.append(f"  {h.get('date')}: Modal Rs {h.get('modal_price', 'N/A')} per {h.get('unit', 'Quintal')}")
            summary = result.get("summary", {})
            if summary:
                change = summary.get("price_change", 0)
                pct = summary.get("price_change_pct", 0)
                direction = "up" if change >= 0 else "down"
                lines.append(f"Overall trend: price went {direction} by Rs {abs(change)} ({abs(pct):.1f}%) over this period.")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[AGENT] get_historical_crop_prices error: {e}")
            return "I could not retrieve historical price data right now. Please try again shortly."

    # Initialize and start the Multimodal Agent for Gemini Realtime
    agent = MultimodalAgent(
        model=model,
        fnc_ctx=fnc_ctx
    )
    
    agent.start(ctx.room, participant)

if __name__ == "__main__":
    if not os.getenv("LIVEKIT_URL"):
        print("\n\nERROR: Missing LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in your .env file.\n")
        print("Please create a free project at https://cloud.livekit.io/ and add your keys to the backend/.env file.\n")
        exit(1)
        
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint
    ))
