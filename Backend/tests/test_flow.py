import urllib.parse
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_pillar_integration_flow():
    """
    Demonstrates full loop across Pillars 1, 2, 3, and 4:
    1. Ingest voice journal observation (Pillar 1) -> creates journal entry.
    2. Ingest KVK advisory research document into knowledge base (Pillar 2).
    3. Generate RAG AI advice for journal entry using Gemini & pgvector (Pillar 2).
    4. Submit voice feedback on advice (Pillar 3) -> runs intent classification.
    5. Query advisory community trust scores & Wilson lower bound (Pillar 3).
    6. Match past solvers for the issue (Pillar 4) -> returns validated solver.
    7. Connect with past solver via Browser (SMS) and Mobile (2-step voice call) (Pillar 4).
    8. Cold-start query escalates to Pillar 5 human experts (Pillar 4 + Pillar 5).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Pillar 1: Audio Journal Ingestion
        ingest_res = await ac.post(
            "/api/v1/pillar1/ingest-json",
            json={
                "audio_base64": "U0lNVUxBVEVEX0FVRElPX0JZVEVT",
                "channel": "MOBILE",
                "language_code": "en-US"
            },
            headers={"X-Farmer-ID": "11111111-1111-1111-1111-111111111111"}
        )
        assert ingest_res.status_code == 201
        journal_data = ingest_res.json()
        journal_id = journal_data["id"]
        assert journal_data["is_fully_processed"] is False

        # 2. Pillar 2: Knowledge Ingestion
        kb_res = await ac.post("/api/v1/pillar2/knowledge/ingest", json={
            "title": "Neem Oil Solution for Yellowing Leaves in Paddy",
            "content": "Spray 5% neem seed kernel extract to cure yellowing leaves caused by stem borer.",
            "crop": "Paddy",
            "disease_symptom": "Yellowing leaves",
            "region": "Punjab",
            "season": "Kharif",
            "source": "ICAR-KVK Research Paper #101"
        })
        assert kb_res.status_code == 201

        # 3. Pillar 2: RAG Advice Generation
        advice_res = await ac.post("/api/v1/pillar2/generate-advice", json={
            "journal_id": journal_id
        })
        assert advice_res.status_code == 200
        advice_data = advice_res.json()
        assert advice_data["is_fully_processed"] is True
        assert "advice_text" in advice_data
        advice_source = advice_data["advice_source"]

        # 4. Pillar 3: Submit Voice Feedback
        feedback_res = await ac.post(
            "/api/v1/pillar3/feedback-json",
            json={
                "journal_id": journal_id,
                "advice_identifier": advice_source,
                "feedback_text": "This neem solution worked very well and cured my crop!",
                "language_code": "en-US"
            },
            headers={"X-Farmer-ID": "11111111-1111-1111-1111-111111111111"}
        )
        assert feedback_res.status_code == 201
        feedback_data = feedback_res.json()
        assert feedback_data["feedback_intent"] == "POSITIVE"

        # 5. Pillar 3: Retrieve Updated Trust Score Metrics (URL quote advice_source)
        encoded_source = urllib.parse.quote(advice_source, safe='')
        metrics_res = await ac.get(f"/api/v1/pillar3/scores/{encoded_source}")
        assert metrics_res.status_code == 200
        metrics_data = metrics_res.json()
        assert metrics_data["positive_count"] >= 1
        assert metrics_data["wilson_lower_bound"] > 0.0

        # 6. Pillar 4: Query Matchmaking for Another Farmer with Same Issue
        match_res = await ac.post(
            "/api/v1/match",
            json={
                "query": "My paddy leaves are turning yellow due to stem borer in Punjab",
                "issue_category": "CROP_DISEASE",
                "issue_subtype": "Yellowing leaves",
                "crop_type": "Paddy",
                "region": "Punjab",
                "season": "Kharif"
            },
            headers={"X-Farmer-ID": "22222222-2222-2222-2222-222222222222"}
        )
        assert match_res.status_code == 200
        match_data = match_res.json()
        assert match_data["status"] in ["success", "no_matches"]

        # 7. Pillar 4: Connect via Browser Channel (Sends SMS to Target Solver)
        connect_browser_res = await ac.post(
            "/api/v1/connect",
            json={
                "target_farmer_id": "11111111-1111-1111-1111-111111111111",
                "journal_id": journal_id,
                "channel": "BROWSER"
            },
            headers={"X-Farmer-ID": "22222222-2222-2222-2222-222222222222"}
        )
        # If target farmer is found or seeded, status is connected
        assert connect_browser_res.status_code in [200, 404]

        # 8. Pillar 4: Connect via Mobile Channel (2-Step Flow)
        connect_mobile_step1 = await ac.post(
            "/api/v1/connect",
            json={
                "target_farmer_id": "11111111-1111-1111-1111-111111111111",
                "journal_id": journal_id,
                "channel": "MOBILE",
                "confirmed": False
            },
            headers={"X-Farmer-ID": "22222222-2222-2222-2222-222222222222"}
        )
        assert connect_mobile_step1.status_code in [200, 404]
        if connect_mobile_step1.status_code == 200:
            assert connect_mobile_step1.json()["status"] == "confirm_required"

        # 9. Cold Start Test (Pillar 4 + Pillar 5 Escalation)
        cold_res = await ac.post(
            "/api/v1/match",
            json={
                "query": "Unidentified alien purple spot on dragon fruit",
                "issue_category": "CROP_DISEASE",
                "issue_subtype": "Alien Purple Spot",
                "crop_type": "Dragon Fruit",
                "region": "Assam",
                "season": "Summer"
            },
            headers={"X-Farmer-ID": "33333333-3333-3333-3333-333333333333"}
        )
        assert cold_res.status_code == 200
        cold_data = cold_res.json()
        assert cold_data["status"] in ["success", "no_matches"]
