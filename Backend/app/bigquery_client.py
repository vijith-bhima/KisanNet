import os
from google.cloud import bigquery
from google.cloud import aiplatform

class BigQueryClient:
    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("FIRESTORE_PROJECT_ID", "kisannet-a0d82")
        self.dataset = os.getenv("BIGQUERY_DATASET", "kisannet")
        
        # Load GCP Credentials from JSON string if provided (Render)
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            from google.oauth2 import service_account
            import json
            info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            self.client = bigquery.Client(project=self.project, credentials=credentials)
        else:
            try:
                # Fallback to local ADC
                self.client = bigquery.Client(project=self.project)
            except Exception as e:
                print(f"Warning: BigQuery not configured properly. Missing GOOGLE_CREDENTIALS_JSON. Error: {e}")
                self.client = None
        
        # Initialize Gemini AI Model using new google.genai package
        from google import genai as google_genai
        self._genai_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def embed_query(self, text):
        """Generate embedding for a query using Gemini."""
        from google import genai as google_genai
        client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text,
        )
        return result.embeddings[0].values


    def rag_search_crop(self, query_text, crop_type=None, top_k=5):
        """RAG search for crop issues."""
        query_embedding = self.embed_query(query_text)
        
        sql = f"""
        WITH query_embedding AS (
            SELECT {list(query_embedding)} AS embedding
        )
        SELECT 
            id, issue_category, issue_subtype, crop_type, symptoms,
            treatment_option_a, treatment_option_b, source, source_url, region_note, data_status,
            1 - (VECTOR_DISTANCE(kb.embedding, qe.embedding) / 2) AS similarity
        FROM `{self.project}.{self.dataset}.knowledge_base` kb
        CROSS JOIN query_embedding qe
        WHERE 1 - (VECTOR_DISTANCE(kb.embedding, qe.embedding) / 2) > 0.70
        """
        if crop_type:
            sql += f" AND (kb.crop_type = '{crop_type}' OR kb.crop_type IS NULL)"
        sql += f" ORDER BY similarity DESC LIMIT {top_k}"
        
        try:
            results = self.client.query(sql).to_dataframe()
            return results.to_dict('records')
        except Exception:
            return []

    def rag_search_scheme(self, query_text, top_k=5):
        """RAG search for government schemes."""
        query_embedding = self.embed_query(query_text)
        
        sql = f"""
        WITH query_embedding AS (
            SELECT {list(query_embedding)} AS embedding
        )
        SELECT 
            external_id, name, description, eligibility, apply_instructions, source, source_url,
            1 - (VECTOR_DISTANCE(skb.embedding, qe.embedding) / 2) AS similarity
        FROM `{self.project}.{self.dataset}.scheme_knowledge_base` skb
        CROSS JOIN query_embedding qe
        WHERE 1 - (VECTOR_DISTANCE(skb.embedding, qe.embedding) / 2) > 0.70
        ORDER BY similarity DESC LIMIT {top_k}
        """
        try:
            results = self.client.query(sql).to_dataframe()
            return results.to_dict('records')
        except Exception:
            return []

    def insert_feedback(self, journal_id, farmer_id, feedback, transcript, confidence):
        """Insert farmer feedback into BigQuery."""
        sql = f"""
        INSERT INTO `{self.project}.{self.dataset}.answer_feedback`
        (journal_id, farmer_id, feedback, raw_spoken_text, stt_confidence)
        VALUES ('{journal_id}', '{farmer_id}', {feedback}, '{transcript}', {confidence})
        """
        self.client.query(sql).result()

    def get_trust_score(self, advice_identifier):
        """Get trust score from BigQuery materialized view."""
        sql = f"""
        SELECT 
            total_unique_farmers,
            positive_votes,
            negative_votes,
            bayesian_score,
            wilson_lower_bound
        FROM `{self.project}.{self.dataset}.trust_scores`
        WHERE advice_identifier = '{advice_identifier}'
        """
        results = self.client.query(sql).to_dataframe()
        return results.to_dict('records')[0] if len(results) > 0 else None

# Initialize a single global instance
bq_client = BigQueryClient()
