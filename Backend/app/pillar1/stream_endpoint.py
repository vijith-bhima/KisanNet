import json
import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

try:
    import websockets
except ImportError:
    websockets = None

from app.google_llm import google_llm_client
from app.bigquery_client import bq_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice Stream (Live)"])

# Shared Persona Instructions
SYSTEM_INSTRUCTION = """
You are KisanNet, a friendly, warm, and highly knowledgeable agricultural AI assistant for farmers in the BRICS region (especially India).
You are talking to a farmer directly on the phone or through the app in real-time.
- Speak naturally, like a human expert.
- Keep your answers concise, practical, and action-oriented. Do not ramble.
- VERY IMPORTANT: Support both Telugu and English seamlessly! If the user speaks in Telugu (e.g. 'నా వరి పంటకు ఆకులు పసుపుగా మారుతున్నాయి'), reply in Telugu. If they speak English, reply in English. If they mix both, understand them naturally.
- Always provide actionable advice (e.g. spray X chemical, use Y fertilizer).
- DO NOT read out markdown asterisks or bullet points. Speak in conversational paragraphs.
- Use your tools `rag_search_crop` and `rag_search_scheme` when asked about crop diseases, fertilizers, or government schemes to fetch accurate ICAR-KVK agricultural guidelines!
"""

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint that bridges the browser/client directly to the 
    Gemini 2.0 Flash Multimodal Live API.
    """
    await websocket.accept()

    api_key = google_llm_client.get_active_api_key()
    if not api_key:
        logger.error("No Gemini API key configured. Disconnecting.")
        await websocket.send_json({"type": "error", "message": "API key not configured"})
        await websocket.close(code=1011)
        return

    if websockets is None:
        logger.error("The 'websockets' python package is required for client streaming.")
        await websocket.send_json({"type": "error", "message": "Missing websockets dependency on server"})
        await websocket.close(code=1011)
        return

    host = "generativelanguage.googleapis.com"
    model = "models/gemini-2.5-flash-native-audio-latest"
    url = f"wss://{host}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"

    # Setup Message
    setup_message = {
        "setup": {
            "model": model,
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Puck" # Default Gemini Voice
                        }
                    }
                }
            },
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "tools": [
                {
                    "functionDeclarations": [
                        {
                            "name": "rag_search_crop",
                            "description": "Searches the agricultural knowledge base for crop issues, diseases, fertilizers, and symptoms.",
                            "parameters": {
                                "type": "OBJECT",
                                "properties": {
                                    "query_text": {"type": "STRING", "description": "The disease symptom or crop issue query (e.g. 'yellow leaves on rice')"},
                                    "crop_type": {"type": "STRING", "description": "The specific crop type if known (e.g. 'rice', 'wheat')"}
                                },
                                "required": ["query_text"]
                            }
                        },
                        {
                            "name": "rag_search_scheme",
                            "description": "Searches the knowledge base for government agricultural schemes, loans, and subsidies.",
                            "parameters": {
                                "type": "OBJECT",
                                "properties": {
                                    "query_text": {"type": "STRING", "description": "The scheme-related query (e.g. 'PM-KISAN eligibility')"}
                                },
                                "required": ["query_text"]
                            }
                        }
                    ]
                }
            ]
        }
    }

    try:
        async with websockets.connect(url) as gemini_ws:
            # 1. Send Setup
            await gemini_ws.send(json.dumps(setup_message))
            
            # Wait for setup complete
            setup_response = await gemini_ws.recv()
            logger.info("Gemini Live API Setup Response received.")

            # Let frontend know we are connected and ready
            await websocket.send_json({"type": "connected"})
            
            # Send an initial silent prompt to trigger the AI to start the conversation immediately
            greeting_msg = {
                "clientContent": {
                    "turns": [
                        {
                            "role": "user",
                            "parts": [{"text": "Hello! The user has just opened the Voice Mode. Please introduce yourself warmly as KisanNet and ask how you can help them today. Speak in the language they have selected."}]
                        }
                    ],
                    "turnComplete": True
                }
            }
            await gemini_ws.send(json.dumps(greeting_msg))

            async def receive_from_client():
                """Reads PCM audio (base64) from Browser and sends to Gemini"""
                try:
                    while True:
                        data = await websocket.receive_json()
                        if "realtimeInput" in data:
                            # Forward directly to Gemini
                            await gemini_ws.send(json.dumps(data))
                        elif "clientContent" in data:
                            # Used for sending interruption or text signals
                            await gemini_ws.send(json.dumps(data))
                except WebSocketDisconnect:
                    logger.info("Client disconnected from /stream.")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")

            async def receive_from_gemini():
                """Reads PCM audio/text/functionCalls from Gemini and sends to Browser or handles tools"""
                try:
                    while True:
                        msg = await gemini_ws.recv()
                        data = json.loads(msg)
                        
                        # Handle Tool Calls
                        if "serverContent" in data and "modelTurn" in data["serverContent"]:
                            parts = data["serverContent"]["modelTurn"].get("parts", [])
                            for part in parts:
                                if "functionCall" in part:
                                    call = part["functionCall"]
                                    name = call.get("name")
                                    args = call.get("args", {})
                                    
                                    logger.info(f"Gemini requested tool call: {name} with args {args}")
                                    
                                    tool_result = []
                                    try:
                                        if name == "rag_search_crop":
                                            query_text = args.get("query_text", "")
                                            crop_type = args.get("crop_type", None)
                                            tool_result = bq_client.rag_search_crop(query_text, crop_type=crop_type, top_k=3)
                                        elif name == "rag_search_scheme":
                                            query_text = args.get("query_text", "")
                                            tool_result = bq_client.rag_search_scheme(query_text, top_k=3)
                                    except Exception as ex:
                                        logger.warning(f"Tool execution failed: {ex}")
                                        tool_result = [{"error": str(ex)}]
                                        
                                    if not tool_result:
                                        tool_result = [{"message": "No matching data found in knowledge base."}]
                                        
                                    # Send tool response back to Gemini
                                    tool_resp = {
                                        "toolResponse": {
                                            "functionResponses": [
                                                {
                                                    "name": name,
                                                    "id": call.get("id", ""),
                                                    "response": {"result": tool_result}
                                                }
                                            ]
                                        }
                                    }
                                    await gemini_ws.send(json.dumps(tool_resp))

                        # Forward raw JSON string back to client for audio/text rendering
                        await websocket.send_text(msg)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Gemini WebSocket closed.")
                except Exception as e:
                    logger.error(f"Error receiving from Gemini: {e}")

            # Run both loops concurrently
            await asyncio.gather(
                receive_from_client(),
                receive_from_gemini()
            )

    except Exception as e:
        logger.error(f"Gemini WebSocket connection error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"Server Error: {str(e)}"})
            await websocket.close(code=1011)
        except:
            pass
