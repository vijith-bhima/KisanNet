import logging
from typing import List, Dict, Optional
from app.bigquery_client import bq_client

logger = logging.getLogger(__name__)

MIN_WILSON_SCORE = 50.0
SIMILARITY_THRESHOLD = 0.70

class MatchingEngine:
    """
    BigQuery-backed Auto-Matching Engine.
    Implements a Hybrid Search Pipeline: Structured -> Semantic (Fallback).
    Ranked by Pillar 3 Trust Score.
    """
    
    async def structured_match(
        self,
        farmer_id: str,
        issue_category: str,
        issue_subtype: Optional[str],
        region: str,
        season: str,
        crop_type: Optional[str] = None,
        min_wilson: float = MIN_WILSON_SCORE,
        limit: int = 5,
    ) -> List[Dict]:
        """Phase 1: Strict structured SQL matching."""
        if not issue_subtype:
            return []

        crop_filter = f"AND j.crop_type = '{crop_type}'" if crop_type else ""

        sql = f"""
        SELECT 
            j.farmer_id, j.farmer_name, j.village,
            j.solution_text, j.crop_type, j.issue_category, j.issue_subtype, j.observation_timestamp,
            t.wilson_lower_bound, t.bayesian_score
        FROM `{bq_client.project}.{bq_client.dataset}.farm_journals_analytics` j
        JOIN `{bq_client.project}.{bq_client.dataset}.trust_scores` t 
          ON j.ai_source = t.advice_identifier
        WHERE j.issue_category = '{issue_category}'
          AND j.issue_subtype = '{issue_subtype}'
          AND j.region = '{region}'
          AND j.season = '{season}'
          {crop_filter}
          AND j.farmer_id != '{farmer_id}'
          AND t.wilson_lower_bound > {min_wilson}
        ORDER BY t.wilson_lower_bound DESC, j.observation_timestamp DESC
        LIMIT {limit}
        """
        try:
            results = bq_client.client.query(sql).to_dataframe()
            return results.to_dict('records')
        except Exception as e:
            logger.error(f"Structured match failed: {e}")
            return []

    async def semantic_match(
        self,
        query: str,
        exclude_farmer_id: str,
        min_wilson: float = MIN_WILSON_SCORE,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = 5,
    ) -> List[Dict]:
        """Phase 2: Semantic vector match using Vertex AI embeddings."""
        try:
            query_embedding = bq_client.embed_query(query)
            
            sql = f"""
            WITH query_embedding AS (
                SELECT {list(query_embedding)} AS embedding
            )
            SELECT 
                si.farmer_id, si.farmer_name, si.village,
                si.solution_text, si.observation_timestamp,
                1 - (VECTOR_DISTANCE(si.embedding, qe.embedding) / 2) AS similarity,
                t.wilson_lower_bound, t.bayesian_score
            FROM `{bq_client.project}.{bq_client.dataset}.solutions_index` si
            CROSS JOIN query_embedding qe
            JOIN `{bq_client.project}.{bq_client.dataset}.trust_scores` t 
              ON si.journal_id = t.journal_id
            WHERE si.farmer_id != '{exclude_farmer_id}'
              AND t.wilson_lower_bound > {min_wilson}
              AND 1 - (VECTOR_DISTANCE(si.embedding, qe.embedding) / 2) > {similarity_threshold}
            ORDER BY t.wilson_lower_bound DESC, similarity DESC
            LIMIT {top_k}
            """
            results = bq_client.client.query(sql).to_dataframe()
            return results.to_dict('records')
        except Exception as e:
            logger.error(f"Semantic match failed: {e}")
            return []

    async def find_matches(
        self,
        farmer_id: str,
        query: str,
        issue_category: str,
        issue_subtype: Optional[str],
        region: str,
        season: str,
        crop_type: Optional[str] = None,
        top_k: int = 3,
    ) -> Dict:
        """Hybrid Search pipeline."""
        structured_results = await self.structured_match(
            farmer_id, issue_category, issue_subtype, region, season, crop_type, limit=top_k
        )

        if len(structured_results) >= top_k:
            return {"source": "structured", "matches": structured_results[:top_k], "count": len(structured_results)}

        semantic_results = await self.semantic_match(query, farmer_id, top_k=top_k)

        # Merge and deduplicate
        merged = []
        seen_farmers = set()
        for m in structured_results + semantic_results:
            if m["farmer_id"] in seen_farmers:
                continue
            seen_farmers.add(m["farmer_id"])
            merged.append(m)

        merged.sort(key=lambda x: (x.get("wilson_lower_bound", 0.0), x.get("similarity", 0.0)), reverse=True)
        is_fallback = len(structured_results) < top_k

        return {
            "source": "semantic_fallback" if is_fallback else "structured",
            "matches": merged[:top_k],
            "count": len(merged),
            "is_fallback": is_fallback,
        }

matching_engine = MatchingEngine()
