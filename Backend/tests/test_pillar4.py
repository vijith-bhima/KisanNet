import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.pillar4.matching_engine import MatchingEngine, _to_pgvector_literal, MIN_WILSON_SCORE, SIMILARITY_THRESHOLD
from app.pillar4.endpoints import get_db_client
from app.pillar4.issue_classifier import issue_classifier
from app.pillar5.escalation import escalation_queue
from app.twilio_service import twilio_client

class MockDatabase:
    def __init__(self):
        self.fetch_mock = AsyncMock(return_value=[])
        self.fetchrow_mock = AsyncMock(return_value=None)
        self.fetchval_mock = AsyncMock(return_value=str(uuid.uuid4()))
        self.execute_mock = AsyncMock(return_value=None)

    async def fetch(self, query: str, *args):
        return await self.fetch_mock(query, *args)

    async def fetchrow(self, query: str, *args):
        return await self.fetchrow_mock(query, *args)

    async def fetchval(self, query: str, *args):
        return await self.fetchval_mock(query, *args)

    async def execute(self, query: str, *args):
        return await self.execute_mock(query, *args)


@pytest.mark.asyncio
async def test_null_subtype_short_circuit():
    """
    Test 1: NULL issue_subtype immediately returns [] without executing any SQL query.
    """
    mock_db = MockDatabase()
    engine = MatchingEngine(mock_db)

    results = await engine.structured_match(
        issue_category="IRRIGATION",
        issue_subtype=None,
        region="Punjab",
        season="Kharif",
        exclude_farmer_id="11111111-1111-1111-1111-111111111111"
    )

    assert results == []
    mock_db.fetch_mock.assert_not_called()


@pytest.mark.asyncio
async def test_structured_match_non_disease_category_and_optional_crop():
    """
    Test 2: Structured match across non-disease categories (e.g. IRRIGATION/DRIP_SYSTEM_CLOG)
    with optional crop_type filter behaving correctly when provided vs omitted (None).
    """
    mock_db = MockDatabase()
    mock_db.fetch_mock.return_value = [
        {
            "farmer_id": "solver-farmer-1",
            "farmer_name": "Ramesh Kumar",
            "village": "Ludhiana",
            "solution_text": "Flushed drip lateral lines with dilute acid treatment",
            "observation_timestamp": "2026-08-10T10:00:00Z",
            "issue_category": "IRRIGATION",
            "wilson_lower_bound": 82.5,
            "bayesian_score": 0.88,
            "vote_count": 14
        },
        {
            "farmer_id": "solver-farmer-2",
            "farmer_name": "Suresh Patel",
            "village": "Amritsar",
            "solution_text": "Installed disc filter before main valve",
            "observation_timestamp": "2026-08-12T10:00:00Z",
            "issue_category": "IRRIGATION",
            "wilson_lower_bound": 74.0,
            "bayesian_score": 0.79,
            "vote_count": 8
        }
    ]
    engine = MatchingEngine(mock_db)

    # 1. Test with crop_type=None (omitted)
    results_no_crop = await engine.structured_match(
        issue_category="IRRIGATION",
        issue_subtype="DRIP_SYSTEM_CLOG",
        region="Punjab",
        season="Kharif",
        exclude_farmer_id="requesting-farmer-123",
        crop_type=None,
        min_wilson=50.0,
        limit=5
    )

    assert len(results_no_crop) == 2
    assert results_no_crop[0]["farmer_name"] == "Ramesh Kumar"
    assert results_no_crop[0]["wilson_lower_bound"] == 82.5
    # Verify SQL parameters passed
    call_args = mock_db.fetch_mock.call_args[0]
    assert call_args[1] == "IRRIGATION"
    assert call_args[2] == "DRIP_SYSTEM_CLOG"
    assert call_args[3] == "Punjab"
    assert call_args[4] == "Kharif"
    assert call_args[5] == "requesting-farmer-123"
    assert call_args[6] == 50.0
    assert call_args[7] is None # crop_type is None

    # 2. Test with crop_type="Sugarcane"
    results_with_crop = await engine.structured_match(
        issue_category="IRRIGATION",
        issue_subtype="DRIP_SYSTEM_CLOG",
        region="Punjab",
        season="Kharif",
        exclude_farmer_id="requesting-farmer-123",
        crop_type="Sugarcane",
        min_wilson=50.0,
        limit=5
    )
    assert len(results_with_crop) == 2
    call_args_crop = mock_db.fetch_mock.call_args[0]
    assert call_args_crop[7] == "Sugarcane"


@pytest.mark.asyncio
async def test_semantic_match_filtering_and_ranking():
    """
    Test 3: Semantic match filters by similarity_threshold (>0.70) and min_wilson (>50.0), self-excluding caller.
    """
    mock_db = MockDatabase()
    mock_db.fetch_mock.return_value = [
        {
            "farmer_id": "solver-3",
            "farmer_name": "Gopal Sharma",
            "village": "Bathinda",
            "solution_text": "Used organic copper spray for leaf curl",
            "issue_category": "CROP_DISEASE",
            "similarity": 0.89,
            "wilson_lower_bound": 88.0,
            "bayesian_score": 0.91,
            "vote_count": 20
        }
    ]
    engine = MatchingEngine(mock_db)

    results = await engine.semantic_match(
        query="curling yellow leaves in tomato",
        exclude_farmer_id="my-farmer-id",
        min_wilson=50.0,
        similarity_threshold=0.70,
        top_k=5
    )

    assert len(results) == 1
    assert results[0]["farmer_name"] == "Gopal Sharma"
    assert results[0]["similarity"] == 0.89
    call_args = mock_db.fetch_mock.call_args[0]
    assert call_args[2] == "my-farmer-id"
    assert call_args[3] == 50.0
    assert call_args[4] == 0.70


@pytest.mark.asyncio
async def test_find_matches_tiered_fallback_and_deduplication():
    """
    Test 4: Tiered matching uses structured match if >= top_k, else falls back to semantic and dedups by farmer_id.
    """
    mock_db = MockDatabase()
    engine = MatchingEngine(mock_db)

    # Scenario A: Structured returns 3 results (top_k=3) -> No semantic fallback needed
    mock_db.fetch_mock.return_value = [
        {"farmer_id": "f1", "farmer_name": "Farmer 1", "wilson_lower_bound": 90.0, "issue_category": "PEST"},
        {"farmer_id": "f2", "farmer_name": "Farmer 2", "wilson_lower_bound": 85.0, "issue_category": "PEST"},
        {"farmer_id": "f3", "farmer_name": "Farmer 3", "wilson_lower_bound": 80.0, "issue_category": "PEST"},
    ]
    res_a = await engine.find_matches(
        farmer_id="user-1",
        query="pink bollworm pest",
        issue_category="PEST",
        issue_subtype="PINK_BOLLWORM",
        region="Punjab",
        season="Kharif",
        crop_type="Cotton",
        top_k=3
    )
    assert res_a["source"] == "structured"
    assert res_a["is_fallback"] is False
    assert len(res_a["matches"]) == 3

    # Scenario B: Structured returns 1 result (< top_k) -> triggers semantic match and merges with dedup
    with patch.object(engine, 'structured_match', new_callable=AsyncMock) as mock_struct, \
         patch.object(engine, 'semantic_match', new_callable=AsyncMock) as mock_sem:
        
        mock_struct.return_value = [
            {"farmer_id": "f1", "farmer_name": "Farmer 1", "wilson_lower_bound": 75.0, "issue_category": "PEST"}
        ]
        mock_sem.return_value = [
            {"farmer_id": "f1", "farmer_name": "Farmer 1", "wilson_lower_bound": 75.0, "similarity": 0.95, "issue_category": "PEST"}, # Duplicate f1
            {"farmer_id": "f2", "farmer_name": "Farmer 2", "wilson_lower_bound": 85.0, "similarity": 0.85, "issue_category": "PEST"}  # New f2
        ]

        res_b = await engine.find_matches(
            farmer_id="user-1",
            query="pink bollworm pest damage",
            issue_category="PEST",
            issue_subtype="PINK_BOLLWORM",
            region="Punjab",
            season="Kharif",
            crop_type="Cotton",
            top_k=3
        )
        assert res_b["source"] == "semantic_fallback"
        assert res_b["is_fallback"] is True
        # Merged list should have f2 (wilson 85) first, then f1 (wilson 75), and NO duplicate f1
        assert len(res_b["matches"]) == 2
        assert res_b["matches"][0]["farmer_id"] == "f2"
        assert res_b["matches"][1]["farmer_id"] == "f1"


@pytest.mark.asyncio
async def test_deprecated_disease_name_alias_support():
    """
    Test 5: Backward compatibility: requests with deprecated disease_name parameter
    are correctly mapped to issue_category='CROP_DISEASE' and issue_subtype=disease_name.
    """
    mock_db = MockDatabase()
    mock_db.fetch_mock.return_value = [
        {
            "farmer_id": "f1",
            "farmer_name": "Farmer 1",
            "village": "Ludhiana",
            "solution_text": "Used bio-fungicide",
            "observation_timestamp": "2026-08-10T10:00:00Z",
            "issue_category": "CROP_DISEASE",
            "wilson_lower_bound": 80.0,
            "bayesian_score": 0.85,
            "vote_count": 10
        }
    ]
    app.dependency_overrides[get_db_client] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/match", json={
            "query": "yellow leaves in paddy",
            "crop_type": "Paddy",
            "disease_name": "Yellow Leaves",  # Using deprecated alias
            "region": "Punjab",
            "season": "Kharif"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert len(data["matches"]) >= 1

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_issue_classifier_fallback_and_classification():
    """
    Test 6: IssueClassifier correctly classifies non-disease queries into appropriate categories.
    """
    # 1. Irrigation query
    cat1, sub1 = await issue_classifier.classify_query("Drip irrigation pipe is clogged with salt")
    assert cat1 == "IRRIGATION"

    # 2. Market price query
    cat2, sub2 = await issue_classifier.classify_query("What is the current mandi market price for wheat?")
    assert cat2 == "MARKET_PRICE"

    # 3. Equipment query
    cat3, sub3 = await issue_classifier.classify_query("Tractor engine failure during field ploughing")
    assert cat3 == "EQUIPMENT"

    # 4. Govt scheme query
    cat4, sub4 = await issue_classifier.classify_query("How to apply for PM-Kisan subsidy scheme?")
    assert cat4 == "GOVT_SCHEME"


@pytest.mark.asyncio
async def test_cold_start_escalation():
    """
    Test 7: Zero matches in both structured and semantic match triggers Pillar 5 human expert escalation.
    """
    mock_db = MockDatabase()
    mock_db.fetch_mock.return_value = []
    app.dependency_overrides[get_db_client] = lambda: mock_db

    initial_tickets_count = len(escalation_queue.escalated_tickets)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/match", json={
            "query": "mysterious purple fungus on quinoa",
            "issue_category": "CROP_DISEASE",
            "issue_subtype": "Purple Fungus",
            "crop_type": "Quinoa",
            "region": "Ladakh",
            "season": "Summer"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "no_matches"
        assert "escalating this to our expert team" in data["message"]
        assert len(escalation_queue.escalated_tickets) == initial_tickets_count + 1
        assert escalation_queue.escalated_tickets[-1]["crop_type"] == "Quinoa"

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_browser_connect_channel_reveals_number_and_sends_sms():
    """
    Test 8: BROWSER channel returns tel: link and sends structured notification SMS to target solver.
    """
    mock_db = MockDatabase()
    mock_db.fetchrow_mock.side_effect = [
        {"name": "Requester Farmer", "phone_number": "+919111111111"}, # Source
        {"name": "Solver Farmer", "phone_number": "+919222222222"}     # Target
    ]
    mock_db.fetchval_mock.return_value = "conn-uuid-123"
    app.dependency_overrides[get_db_client] = lambda: mock_db

    initial_msgs = len(twilio_client.messages.sent_messages)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/connect", json={
            "target_farmer_id": "target-uuid-456",
            "journal_id": "journal-uuid-789",
            "channel": "BROWSER"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "connected"
        assert data["target_name"] == "Solver Farmer"
        assert data["tel_link"] == "tel:+919222222222"
        assert len(twilio_client.messages.sent_messages) == initial_msgs + 1
        last_sms = twilio_client.messages.sent_messages[-1]
        assert last_sms["to"] == "+919222222222"
        assert "Farmer Requester Farmer needs help with crop advisory" in last_sms["body"]
        assert "Please call them at +919111111111" in last_sms["body"]

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_mobile_connect_channel_two_step_confirmation():
    """
    Test 9: MOBILE channel requires confirmed=False -> confirm_required (no DB insert/call), then confirmed=True dials.
    """
    mock_db = MockDatabase()
    mock_db.fetchrow_mock.side_effect = [
        # Call 1 (unconfirmed)
        {"name": "Requester Farmer", "phone_number": "+919111111111"},
        {"name": "Solver Farmer", "phone_number": "+919222222222"},
        # Call 2 (confirmed)
        {"name": "Requester Farmer", "phone_number": "+919111111111"},
        {"name": "Solver Farmer", "phone_number": "+919222222222"},
    ]
    mock_db.fetchval_mock.return_value = "conn-mobile-uuid"
    app.dependency_overrides[get_db_client] = lambda: mock_db

    initial_calls = len(twilio_client.calls.created_calls)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Unconfirmed request
        res1 = await ac.post("/api/v1/connect", json={
            "target_farmer_id": "target-uuid-456",
            "journal_id": "journal-uuid-789",
            "channel": "MOBILE",
            "confirmed": False
        })
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "confirm_required"
        assert data1["prompt"] == "Call Solver Farmer now?"
        # Verify NO calls placed and NO DB insert called yet
        assert len(twilio_client.calls.created_calls) == initial_calls
        mock_db.fetchval_mock.assert_not_called()

        # Step 2: Confirmed request
        res2 = await ac.post("/api/v1/connect", json={
            "target_farmer_id": "target-uuid-456",
            "journal_id": "journal-uuid-789",
            "channel": "MOBILE",
            "confirmed": True
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "connected"
        assert data2["message"] == "Connecting you to Solver Farmer..."
        assert len(twilio_client.calls.created_calls) == initial_calls + 1
        last_call = twilio_client.calls.created_calls[-1]
        assert last_call["to"] == "+919111111111" # Dials source farmer
        assert "+919222222222" in last_call["twiml"] # Connects to target farmer

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_duplicate_connect_idempotency():
    """
    Test 10: Retried / duplicate connection request returns status connected but does NOT re-notify or re-dial (inserted_id is None).
    """
    mock_db = MockDatabase()
    mock_db.fetchrow_mock.side_effect = [
        {"name": "Requester Farmer", "phone_number": "+919111111111"},
        {"name": "Solver Farmer", "phone_number": "+919222222222"}
    ]
    # ON CONFLICT DO NOTHING returns None
    mock_db.fetchval_mock.return_value = None
    app.dependency_overrides[get_db_client] = lambda: mock_db

    initial_msgs = len(twilio_client.messages.sent_messages)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/connect", json={
            "target_farmer_id": "target-uuid-456",
            "journal_id": "journal-uuid-789",
            "channel": "BROWSER"
        })
        assert res.status_code == 200
        # No new SMS sent because inserted_id is None
        assert len(twilio_client.messages.sent_messages) == initial_msgs

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_twilio_voice_no_answer_sms_fallback():
    """
    Test 11: Twilio voice call webhook with DialCallStatus != completed triggers SMS fallback to target solver.
    """
    mock_db = MockDatabase()
    mock_db.fetchrow_mock.return_value = {
        "target_farmer_id": "target-uuid",
        "source_farmer_id": "source-uuid",
        "target_phone": "+919222222222",
        "target_name": "Solver Farmer",
        "source_name": "Requester Farmer",
        "source_phone": "+919111111111"
    }
    app.dependency_overrides[get_db_client] = lambda: mock_db

    initial_msgs = len(twilio_client.messages.sent_messages)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/voice/connect-status?connection_id=conn-123",
            data={"DialCallStatus": "no-answer"}
        )
        assert res.status_code == 200
        assert res.json() == {"status": "recorded"}

        # Verify fallback SMS sent to target solver
        assert len(twilio_client.messages.sent_messages) == initial_msgs + 1
        last_sms = twilio_client.messages.sent_messages[-1]
        assert last_sms["to"] == "+919222222222"
        assert "Farmer Requester Farmer needs help with crop advisory" in last_sms["body"]

        # Verify DB updated with connection_method = 'SMS_FALLBACK'
        executed_sqls = [c[0][0] for c in mock_db.execute_mock.call_args_list]
        assert any("SMS_FALLBACK" in sql for sql in executed_sqls)

    app.dependency_overrides.pop(get_db_client, None)


@pytest.mark.asyncio
async def test_ingest_solution_embedding():
    """
    Test 12: ingest_solution_embedding generates 384-dim embedding and runs UPSERT query into solution_embeddings.
    """
    mock_db = MockDatabase()
    engine = MatchingEngine(mock_db)

    await engine.ingest_solution_embedding(
        journal_id="j-uuid-1",
        farmer_id="f-uuid-1",
        solution_text="Flushed drip lateral lines with dilute acid treatment"
    )

    mock_db.execute_mock.assert_called_once()
    sql_arg = mock_db.execute_mock.call_args[0][0]
    assert "INSERT INTO solution_embeddings" in sql_arg
    assert "ON CONFLICT (journal_id) DO UPDATE" in sql_arg
    params = mock_db.execute_mock.call_args[0]
    assert params[1] == "j-uuid-1"
    assert params[2] == "f-uuid-1"
    assert params[3] == "Flushed drip lateral lines with dilute acid treatment"
    assert params[4].startswith("[") and params[4].endswith("]")
