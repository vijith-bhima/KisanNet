"""
Standalone test: does this API key have access to Gemini Live API at all?
Run this directly: python test_gemini_live.py
Bypasses LiveKit entirely so we know if the problem is the key/project/region
or something in the LiveKit plugin.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set in environment")
        return

    client = genai.Client(api_key=api_key)

    models_to_try = [
        "gemini-2.5-flash-native-audio-preview-12-2025",
    ]

    for model in models_to_try:
        print(f"\n--- Attempting model: {model} ---")
        try:
            async with client.aio.live.connect(
                model=model,
                config=types.LiveConnectConfig(
                    response_modalities=[types.Modality.AUDIO],
                ),
            ) as session:
                print(f"SUCCESS with {model}: Live API connection established.")
                await session.send_client_content(
                    turns=types.Content(
                        role="user", parts=[types.Part(text="Say hi in one word.")]
                    )
                )
                got_audio = False
                async for response in session.receive():
                    if response.data is not None:
                        got_audio = True
                    if response.server_content and response.server_content.turn_complete:
                        break
                print(f"Received audio bytes: {got_audio}")
                return
        except Exception as e:
            print(f"FAILED with {model}: {type(e).__name__}: {e}")

    print("\nAll model attempts failed.")

if __name__ == "__main__":
    asyncio.run(main())