import base64
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from app.google_llm import google_llm_client
import httpx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["Pillar 1: Vision Analysis"])

@router.post("/analyze")
async def analyze_leaf_image(
    file: UploadFile = File(...),
    language_code: str = Form("en-US")
):
    """
    Decoupled vision endpoint for analyzing crop images using Gemini Multimodal.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {e}")

    # 1. First, attempt to use the local PyTorch ResNet-9 model (Hackathon integration)
    try:
        from app.pillar1.resnet_model import predict_disease
        resnet_prediction = predict_disease(image_bytes)
        if resnet_prediction:
            # Parse the ResNet-9 class format e.g., "Tomato___Late_blight"
            parts = resnet_prediction.split("___")
            crop = parts[0]
            disease = parts[1].replace("_", " ") if len(parts) > 1 else "Unknown"
            return {
                "crop": crop,
                "disease_symptom": disease,
                "confidence": 0.99, # ResNet-9 offline prediction
                "source": "ResNet-9 Offline Model"
            }
    except Exception as e:
        logger.warning(f"ResNet9 inference failed or not configured, falling back to Gemini: {e}")

    # 2. Fallback to Gemini Multimodal Live API
    api_key = google_llm_client.get_active_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured and ResNet-9 model not found.")

    prompt = (
        "You are an expert agricultural botanist. "
        "Look at this image of a crop leaf or plant. "
        "Identify the crop name and any visible disease, pest, or nutrient deficiency symptom. "
        "Respond in strictly valid JSON format matching this schema: "
        '{"crop": "Crop Name", "disease_symptom": "Symptom Name", "confidence": 0.95}'
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": file.content_type,
                        "data": image_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Gemini Vision API error: {resp.text}")
                raise HTTPException(status_code=500, detail="Vision AI analysis failed.")
            
            resp_json = resp.json()
            raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            
            # Simple cleanup in case it has markdown ticks
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            import json
            parsed = json.loads(raw_text)
            return parsed

        except Exception as e:
            logger.error(f"Vision analysis request failed: {e}")
            raise HTTPException(status_code=500, detail="Error communicating with Vision AI.")
