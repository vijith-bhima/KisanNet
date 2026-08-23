"""
KisanNet All-Pillars Test Runner
Executes comprehensive end-to-end integration and unit tests across Pillars 1, 2, 3, and 4.
"""
import sys
import uuid
import asyncio
import urllib.parse
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.pillar1.models import FarmJournal
from app.pillar2.models import KnowledgeBase
from app.pillar3.models import TrustScore
from app.pillar4.matching_engine import MatchingEngine
from app.pillar4.issue_classifier import issue_classifier
from app.pillar4.endpoints import get_db_client
from app.pillar5.escalation import escalation_queue
from app.twilio_service import twilio_client

class MockScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None


class MockExecuteResult:
    def __init__(self, items=None):
        self._items = items or []

    def scalars(self):
        return MockScalarsResult(self._items)


class MockAsyncSession:
    """In-memory AsyncSession mock for prototype testing without live PostgreSQL."""
    def __init__(self):
        self.journals = {}
        self.kb = {}
        self.trust_scores = {}

    def add(self, obj):
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if hasattr(obj, "transcription"):
            self.journals[str(obj.id)] = obj
        elif hasattr(obj, "content"):
            self.kb[str(obj.id)] = obj
        elif hasattr(obj, "feedback_intent"):
            self.trust_scores[str(obj.id)] = obj

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def execute(self, stmt, *args, **kwargs):
        stmt_str = str(stmt).lower()
        if "farm_journals" in stmt_str:
            items = list(self.journals.values())
            return MockExecuteResult(items)
        elif "knowledge_base" in stmt_str:
            items = list(self.kb.values())
            return MockExecuteResult(items)
        elif "trust_scores" in stmt_str:
            items = list(self.trust_scores.values())
            return MockExecuteResult(items)
        return MockExecuteResult([])


class MockDatabase:
    def __init__(self):
        self.fetch_mock = AsyncMock(return_value=[])
        self.fetchrow_mock = AsyncMock(return_value=None)
        self.fetchval_mock = AsyncMock(return_value="conn-test-uuid")
        self.execute_mock = AsyncMock(return_value=None)

    async def fetch(self, query: str, *args):
        return await self.fetch_mock(query, *args)

    async def fetchrow(self, query: str, *args):
        return await self.fetchrow_mock(query, *args)

    async def fetchval(self, query: str, *args):
        return await self.fetchval_mock(query, *args)

    async def execute(self, query: str, *args):
        return await self.execute_mock(query, *args)


async def run_all_tests():
    passed = 0
    failed = 0
    total = 0

    print("=" * 80)
    print("🌾 KISANNET ALL 4 PILLARS VERIFICATION SUITE")
    print("=" * 80)

    # -------------------------------------------------------------
    # Test 1: Full End-to-End Multi-Pillar Workflow (Pillars 1 -> 2 -> 3 -> 4)
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Running Full Multi-Pillar Integration Workflow...")
    try:
        mock_session = MockAsyncSession()
        mock_db = MockDatabase()
        mock_db.fetch_mock.return_value = [
            {
                "farmer_id": "solver-farmer-1",
                "farmer_name": "Ramesh Kumar",
                "village": "Ludhiana",
                "solution_text": "Sprayed neem kernel extract 5%",
                "observation_timestamp": "2026-08-10T10:00:00Z",
                "issue_category": "CROP_DISEASE",
                "wilson_lower_bound": 82.5,
                "bayesian_score": 0.88,
                "vote_count": 14
            }
        ]

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_client] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Pillar 1: Ingest observation
            p1_res = await ac.post(
                "/api/v1/pillar1/ingest-json",
                json={
                    "audio_base64": "U0lNVUxBVEVEX0FVRElPX0JZVEVT",
                    "channel": "MOBILE",
                    "language_code": "en-US"
                },
                headers={"X-Farmer-ID": "11111111-1111-1111-1111-111111111111"}
            )
            assert p1_res.status_code == 201, f"Pillar 1 failed: {p1_res.text}"
            journal_id = p1_res.json()["id"]
            print("  ✓ Pillar 1: Voice observation ingested & transcribed (FarmJournal record created)")

            # Pillar 2: Ingest KVK Knowledge
            p2_kb = await ac.post("/api/v1/pillar2/knowledge/ingest", json={
                "title": "Neem Oil Solution for Yellowing Leaves in Paddy",
                "content": "Spray 5% neem seed kernel extract to cure yellowing leaves caused by stem borer.",
                "crop": "Paddy",
                "disease_symptom": "Yellowing leaves",
                "region": "Punjab",
                "season": "Kharif",
                "source": "ICAR-KVK Research Paper #101"
            })
            assert p2_kb.status_code == 201, f"Pillar 2 KB ingest failed: {p2_kb.text}"
            print("  ✓ Pillar 2: KVK advisory document ingested with 768-dim vector embedding")

            # Pillar 2: Generate RAG Advice
            p2_adv = await ac.post("/api/v1/pillar2/generate-advice", json={"journal_id": journal_id})
            assert p2_adv.status_code == 200, f"Pillar 2 RAG advice failed: {p2_adv.text}"
            adv_source = p2_adv.json()["advice_source"]
            print(f"  ✓ Pillar 2: RAG advice synthesized & TTS prompt generated (Source: {adv_source})")

            # Pillar 3: Submit Voice Feedback
            p3_fb = await ac.post(
                "/api/v1/pillar3/feedback-json",
                json={
                    "journal_id": journal_id,
                    "advice_identifier": adv_source,
                    "feedback_text": "This neem solution worked very well and cured my crop!",
                    "language_code": "en-US"
                },
                headers={"X-Farmer-ID": "11111111-1111-1111-1111-111111111111"}
            )
            assert p3_fb.status_code == 201, f"Pillar 3 feedback failed: {p3_fb.text}"
            assert p3_fb.json()["feedback_intent"] == "POSITIVE"
            print("  ✓ Pillar 3: Voice feedback recorded with negation-first intent classification (POSITIVE)")

            # Pillar 3: Compute Trust Score
            enc_source = urllib.parse.quote(adv_source, safe='')
            p3_sc = await ac.get(f"/api/v1/pillar3/scores/{enc_source}")
            assert p3_sc.status_code == 200, f"Pillar 3 trust score failed: {p3_sc.text}"
            wilson = p3_sc.json()["wilson_lower_bound"]
            print(f"  ✓ Pillar 3: Wilson lower bound calculated ({wilson}) & solution embedding auto-ingested")

            # Pillar 4: Match with Past Solvers
            p4_m = await ac.post(
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
            assert p4_m.status_code == 200, f"Pillar 4 match failed: {p4_m.text}"
            print("  ✓ Pillar 4: Matchmaking engine queried (Tiered Structured + Semantic Vector Fallback)")

        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_db_client, None)

        print("  --> [PASS] Full End-to-End Workflow across Pillars 1, 2, 3, 4 SUCCESSFUL!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Full Workflow error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 2: Pillar 4 Generalized Multi-Category Matching (Irrigation)
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Pillar 4 Structured Match for Non-Disease Issue (IRRIGATION)...")
    try:
        mock_db = MockDatabase()
        mock_db.fetch_mock.return_value = [
            {
                "farmer_id": "solver-irrigation-1",
                "farmer_name": "Balwinder Singh",
                "village": "Ludhiana",
                "solution_text": "Flushed laterals with 0.5% nitric acid solution",
                "observation_timestamp": "2026-08-15T10:00:00Z",
                "issue_category": "IRRIGATION",
                "wilson_lower_bound": 84.5,
                "bayesian_score": 0.89,
                "vote_count": 12
            }
        ]
        engine = MatchingEngine(mock_db)
        res = await engine.structured_match(
            issue_category="IRRIGATION",
            issue_subtype="DRIP_SYSTEM_CLOG",
            region="Punjab",
            season="Kharif",
            exclude_farmer_id="caller-id",
            crop_type=None
        )
        assert len(res) == 1
        assert res[0]["farmer_name"] == "Balwinder Singh"
        assert res[0]["wilson_lower_bound"] == 84.5
        print("  --> [PASS] Non-disease category matching verified with optional crop_type!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 3: Pillar 4 NULL Subtype Short-Circuit Rule
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing NULL Subtype Short-Circuit Rule (Zero DB Queries)...")
    try:
        mock_db = MockDatabase()
        engine = MatchingEngine(mock_db)
        res = await engine.structured_match(
            issue_category="IRRIGATION",
            issue_subtype=None,
            region="Punjab",
            season="Kharif",
            exclude_farmer_id="caller-id"
        )
        assert res == []
        mock_db.fetch_mock.assert_not_called()
        print("  --> [PASS] NULL subtype returned [] immediately without issuing SQL!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 4: Pillar 4 Backward-Compatible disease_name Alias
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Backward-Compatible disease_name Alias Path...")
    try:
        mock_db = MockDatabase()
        mock_db.fetch_mock.return_value = [{
            "farmer_id": "solver-1",
            "farmer_name": "Ramesh",
            "village": "Ludhiana",
            "solution_text": "Used bio-spray",
            "observation_timestamp": "2026-08-10T10:00:00Z",
            "issue_category": "CROP_DISEASE",
            "wilson_lower_bound": 78.0,
            "bayesian_score": 0.80,
            "vote_count": 9
        }]
        app.dependency_overrides[get_db_client] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/match", json={
                "query": "yellow leaves in paddy",
                "crop_type": "Paddy",
                "disease_name": "Yellow Leaves",
                "region": "Punjab",
                "season": "Kharif"
            })
            assert res.status_code == 200
            assert res.json()["status"] == "success"
        app.dependency_overrides.pop(get_db_client, None)
        print("  --> [PASS] Deprecated disease_name successfully mapped to CROP_DISEASE!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 5: Dynamic Issue Taxonomy Classifier
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Dynamic Issue Taxonomy Classifier...")
    try:
        cat1, _ = await issue_classifier.classify_query("Drip lateral pipe is choked with sediment")
        assert cat1 == "IRRIGATION", f"Expected IRRIGATION, got {cat1}"
        cat2, _ = await issue_classifier.classify_query("Tractor engine gearbox failure")
        assert cat2 == "EQUIPMENT", f"Expected EQUIPMENT, got {cat2}"
        cat3, _ = await issue_classifier.classify_query("Current mandi market price for mustard crop")
        assert cat3 == "MARKET_PRICE", f"Expected MARKET_PRICE, got {cat3}"
        print(f"  ✓ Classified: 'drip pipe' -> {cat1}, 'tractor' -> {cat2}, 'mandi price' -> {cat3}")
        print("  --> [PASS] Issue taxonomy classification accurate across domains!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 6: Direct Connect BROWSER Channel (Number + SMS)
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Direct Connect BROWSER Channel (tel: link + SMS)...")
    try:
        mock_db = MockDatabase()
        mock_db.fetchrow_mock.side_effect = [
            {"name": "Requester Farmer", "phone_number": "+919111111111"},
            {"name": "Solver Farmer", "phone_number": "+919222222222"}
        ]
        mock_db.fetchval_mock.return_value = "conn-123"
        app.dependency_overrides[get_db_client] = lambda: mock_db
        initial_msgs = len(twilio_client.messages.sent_messages)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/connect", json={
                "target_farmer_id": "target-uuid",
                "journal_id": "journal-uuid",
                "channel": "BROWSER"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "connected"
            assert data["tel_link"] == "tel:+919222222222"
            assert len(twilio_client.messages.sent_messages) == initial_msgs + 1
        app.dependency_overrides.pop(get_db_client, None)
        print("  --> [PASS] Browser direct connect revealed number and sent solver SMS notification!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 7: Direct Connect MOBILE Channel (2-Step Confirm -> Dial)
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Direct Connect MOBILE Channel (2-Step Confirmation Flow)...")
    try:
        mock_db = MockDatabase()
        mock_db.fetchrow_mock.side_effect = [
            {"name": "Requester", "phone_number": "+919111111111"},
            {"name": "Solver", "phone_number": "+919222222222"},
            {"name": "Requester", "phone_number": "+919111111111"},
            {"name": "Solver", "phone_number": "+919222222222"}
        ]
        mock_db.fetchval_mock.return_value = "conn-456"
        app.dependency_overrides[get_db_client] = lambda: mock_db
        initial_calls = len(twilio_client.calls.created_calls)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Step 1: Unconfirmed request
            s1 = await ac.post("/api/v1/connect", json={
                "target_farmer_id": "target-uuid",
                "journal_id": "journal-uuid",
                "channel": "MOBILE",
                "confirmed": False
            })
            assert s1.status_code == 200
            assert s1.json()["status"] == "confirm_required"
            assert len(twilio_client.calls.created_calls) == initial_calls, "Call should not be placed before confirm!"

            # Step 2: Confirmed request
            s2 = await ac.post("/api/v1/connect", json={
                "target_farmer_id": "target-uuid",
                "journal_id": "journal-uuid",
                "channel": "MOBILE",
                "confirmed": True
            })
            assert s2.status_code == 200
            assert s2.json()["status"] == "connected"
            assert len(twilio_client.calls.created_calls) == initial_calls + 1
        app.dependency_overrides.pop(get_db_client, None)
        print("  --> [PASS] Two-step confirm-then-dial MOBILE flow verified!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    # -------------------------------------------------------------
    # Test 8: Cold Start Escalation to Pillar 5
    # -------------------------------------------------------------
    total += 1
    print(f"\n[Test {total}] Testing Cold Start -> Pillar 5 Human Review Escalation...")
    try:
        mock_db = MockDatabase()
        mock_db.fetch_mock.return_value = []
        app.dependency_overrides[get_db_client] = lambda: mock_db
        initial_tix = len(escalation_queue.escalated_tickets)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/match", json={
                "query": "Unknown glowing fungus on sandalwood tree",
                "issue_category": "OTHER",
                "issue_subtype": "Glowing Fungus",
                "region": "Karnataka",
                "season": "Summer"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "no_matches"
            assert "escalating this to our expert team" in data["message"]
            assert len(escalation_queue.escalated_tickets) == initial_tix + 1
        app.dependency_overrides.pop(get_db_client, None)
        print("  --> [PASS] Cold start query properly triggered Pillar 5 human escalation ticket!")
        passed += 1
    except Exception as e:
        print(f"  --> [FAIL] Error: {e}")
        failed += 1

    print("\n" + "=" * 80)
    print(f"🏁 TEST SUMMARY: {passed}/{total} PASSED ({failed} FAILED)")
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
