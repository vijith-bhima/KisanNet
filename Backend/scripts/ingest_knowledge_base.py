import os
import json
import sys
import logging
from google.cloud import bigquery
from google.cloud import aiplatform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BIGQUERY_DATASET", "kisannet")
    
    if not project:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable is missing.")
        sys.exit(1)

    # Initialize BigQuery Client
    bq_client = bigquery.Client(project=project)
    dataset_ref = f"{project}.{dataset_id}"

    # Initialize Vertex AI for embeddings
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    model_name = os.getenv("VERTEX_AI_EMBEDDING_MODEL", "text-embedding-004")
    
    try:
        aiplatform.init(project=project, location=location)
        embedder = aiplatform.TextEmbeddingModel.from_pretrained(model_name)
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI: {e}")
        sys.exit(1)

    def get_embedding(text):
        return embedder.get_embeddings([text])[0].values

    # File paths
    kb_path = os.path.join("data", "seed", "knowledge_base.json")
    schemes_path = os.path.join("data", "seed", "schemes.json")

    # 0. Ensure tables exist
    kb_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("issue_category", "STRING"),
        bigquery.SchemaField("issue_subtype", "STRING"),
        bigquery.SchemaField("crop_type", "STRING"),
        bigquery.SchemaField("symptoms", "STRING"),
        bigquery.SchemaField("treatment_option_a", "JSON"),
        bigquery.SchemaField("treatment_option_b", "JSON"),
        bigquery.SchemaField("source", "STRING"),
        bigquery.SchemaField("source_url", "STRING"),
        bigquery.SchemaField("region_note", "STRING"),
        bigquery.SchemaField("data_status", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED")
    ]
    kb_table = bigquery.Table(f"{dataset_ref}.knowledge_base", schema=kb_schema)
    bq_client.create_table(kb_table, exists_ok=True)

    scheme_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("external_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("eligibility", "STRING"),
        bigquery.SchemaField("apply_instructions", "STRING"),
        bigquery.SchemaField("source", "STRING"),
        bigquery.SchemaField("source_url", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED")
    ]
    scheme_table = bigquery.Table(f"{dataset_ref}.scheme_knowledge_base", schema=scheme_schema)
    bq_client.create_table(scheme_table, exists_ok=True)

    # 1. Ingest Knowledge Base (Crops/Diseases)
    if os.path.exists(kb_path):
        with open(kb_path, 'r') as f:
            kb_data = json.load(f)
        
        kb_inserted = 0
        for entry in kb_data:
            try:
                # Build embedding text
                crop = entry.get('crop', '')
                disease = entry.get('disease', '')
                symptoms = entry.get('symptoms', '')
                embed_text = f"{crop} - {disease}: {symptoms}"
                embedding = get_embedding(embed_text)

                # Prepare row for BigQuery DML
                # Using MERGE for idempotency based on id
                merge_sql = f"""
                MERGE `{dataset_ref}.knowledge_base` T
                USING (
                    SELECT 
                        @id AS id, 
                        'CROP_DISEASE' AS issue_category, 
                        @issue_subtype AS issue_subtype, 
                        @crop_type AS crop_type, 
                        @symptoms AS symptoms, 
                        @treatment_option_a AS treatment_option_a, 
                        @treatment_option_b AS treatment_option_b, 
                        @source AS source, 
                        @source_url AS source_url, 
                        @region_note AS region_note, 
                        @data_status AS data_status, 
                        @embedding AS embedding
                ) S
                ON T.id = S.id
                WHEN MATCHED THEN
                    UPDATE SET 
                        issue_category=S.issue_category, issue_subtype=S.issue_subtype, crop_type=S.crop_type, 
                        symptoms=S.symptoms, treatment_option_a=S.treatment_option_a, treatment_option_b=S.treatment_option_b, 
                        source=S.source, source_url=S.source_url, region_note=S.region_note, data_status=S.data_status, 
                        embedding=S.embedding
                WHEN NOT MATCHED THEN
                    INSERT (id, issue_category, issue_subtype, crop_type, symptoms, treatment_option_a, treatment_option_b, source, source_url, region_note, data_status, embedding)
                    VALUES(S.id, S.issue_category, S.issue_subtype, S.crop_type, S.symptoms, S.treatment_option_a, S.treatment_option_b, S.source, S.source_url, S.region_note, S.data_status, S.embedding)
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("id", "STRING", entry["id"]),
                        bigquery.ScalarQueryParameter("issue_subtype", "STRING", disease),
                        bigquery.ScalarQueryParameter("crop_type", "STRING", crop),
                        bigquery.ScalarQueryParameter("symptoms", "STRING", symptoms),
                        bigquery.ScalarQueryParameter("treatment_option_a", "JSON", json.dumps(entry.get("treatment_option_a", {}))),
                        bigquery.ScalarQueryParameter("treatment_option_b", "JSON", json.dumps(entry.get("treatment_option_b", {}))),
                        bigquery.ScalarQueryParameter("source", "STRING", entry.get("source")),
                        bigquery.ScalarQueryParameter("source_url", "STRING", entry.get("source_url")),
                        bigquery.ScalarQueryParameter("region_note", "STRING", entry.get("region")),
                        bigquery.ScalarQueryParameter("data_status", "STRING", entry.get("data_status")),
                        bigquery.ArrayQueryParameter("embedding", "FLOAT64", embedding),
                    ]
                )
                bq_client.query(merge_sql, job_config=job_config).result()
                kb_inserted += 1
            except Exception as e:
                logger.error(f"Failed to ingest knowledge_base entry {entry.get('id')}: {e}")
                sys.exit(1)
        
        logger.info(f"Successfully upserted {kb_inserted} knowledge base entries.")

    # 2. Ingest Schemes
    if os.path.exists(schemes_path):
        with open(schemes_path, 'r') as f:
            schemes_data = json.load(f)
        
        schemes_inserted = 0
        for entry in schemes_data:
            try:
                # Build embedding text
                name = entry.get('name', '')
                description = entry.get('description', '')
                eligibility = entry.get('eligibility', '')
                embed_text = f"{name} - {description}: {eligibility}"
                embedding = get_embedding(embed_text)

                # Using MERGE for idempotency based on external_id
                merge_sql = f"""
                MERGE `{dataset_ref}.scheme_knowledge_base` T
                USING (
                    SELECT 
                        @external_id AS external_id, 
                        @name AS name, 
                        @description AS description, 
                        @eligibility AS eligibility, 
                        @apply_instructions AS apply_instructions, 
                        @source AS source, 
                        @source_url AS source_url, 
                        @embedding AS embedding
                ) S
                ON T.external_id = S.external_id
                WHEN MATCHED THEN
                    UPDATE SET 
                        name=S.name, description=S.description, eligibility=S.eligibility, 
                        apply_instructions=S.apply_instructions, source=S.source, source_url=S.source_url, 
                        embedding=S.embedding
                WHEN NOT MATCHED THEN
                    INSERT (id, external_id, name, description, eligibility, apply_instructions, source, source_url, embedding)
                    VALUES(GENERATE_UUID(), S.external_id, S.name, S.description, S.eligibility, S.apply_instructions, S.source, S.source_url, S.embedding)
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("external_id", "STRING", entry["id"]),
                        bigquery.ScalarQueryParameter("name", "STRING", name),
                        bigquery.ScalarQueryParameter("description", "STRING", description),
                        bigquery.ScalarQueryParameter("eligibility", "STRING", eligibility),
                        bigquery.ScalarQueryParameter("apply_instructions", "STRING", entry.get("apply")),
                        bigquery.ScalarQueryParameter("source", "STRING", entry.get("source")),
                        bigquery.ScalarQueryParameter("source_url", "STRING", entry.get("source_url")),
                        bigquery.ArrayQueryParameter("embedding", "FLOAT64", embedding),
                    ]
                )
                bq_client.query(merge_sql, job_config=job_config).result()
                schemes_inserted += 1
            except Exception as e:
                logger.error(f"Failed to ingest scheme entry {entry.get('id')}: {e}")
                sys.exit(1)

        logger.info(f"Successfully upserted {schemes_inserted} scheme entries.")

if __name__ == "__main__":
    main()
