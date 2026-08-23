import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

let aiClient: GoogleGenAI | null = null;
function getAI(): GoogleGenAI | null {
  if (!aiClient && process.env.GEMINI_API_KEY) {
    try {
      aiClient = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    } catch (e) {
      console.warn('Gemini client init note:', e);
    }
  }
  return aiClient;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query } = body;

    const ai = getAI();
    if (!ai) {
      return NextResponse.json({ 
        response: 'API key is missing or invalid. Please check your .env.local file.',
        error: 'Missing GEMINI_API_KEY'
      });
    }

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [
        {
          role: 'user',
          parts: [{
            text: `You are KisanNet Voice Assistant, a friendly female agricultural expert. 
Answer in a warm, natural conversational style in Telugu. Keep it brief.
User asked: ${query}`
          }]
        }
      ]
    });

    return NextResponse.json({ response: response.text });
  } catch (error) {
    console.error('Error in voice assistant route:', error);
    return NextResponse.json(
      { response: 'క్షమించండి, నాకు కొంచెం ఇబ్బందిగా ఉంది. దయచేసి మళ్లీ ప్రయత్నించండి.', error: String(error) },
      { status: 500 }
    );
  }
}
