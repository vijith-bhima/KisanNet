import { NextRequest } from "next/server";
import { GoogleGenAI } from "@google/genai";
import fs from "fs";
import path from "path";

let aiClient: GoogleGenAI | null = null;
function getAI(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!aiClient && apiKey) {
    try {
      aiClient = new GoogleGenAI({ apiKey });
    } catch (e) {
      console.warn('Gemini client init note:', e);
    }
  }
  return aiClient;
}

export const dynamic = 'force-dynamic';

// Define a simple RAG loader that reads the JSON files
function getLocalRAGContext(query: string) {
  try {
    const baseDir = path.resolve(process.cwd(), "..", "my data");
    const kbPath = path.join(baseDir, "knowledge_base.json");
    const schemesPath = path.join(baseDir, "schemes.json");

    let contextText = "";

    // A very simple keyword matcher
    const keywords = query.toLowerCase().match(/\w{4,}/g) || [];
    
    if (keywords.length === 0) return "";

    if (fs.existsSync(kbPath)) {
      const kbData = JSON.parse(fs.readFileSync(kbPath, "utf-8"));
      const matched = kbData.filter((item: any) => {
        const text = `${item.crop} ${item.disease} ${item.symptoms}`.toLowerCase();
        return keywords.some(kw => text.includes(kw));
      });
      if (matched.length > 0) {
        contextText += "Relevant Farming Knowledge:\n" + JSON.stringify(matched.slice(0, 3), null, 2) + "\n\n";
      }
    }

    if (fs.existsSync(schemesPath)) {
      const schemesData = JSON.parse(fs.readFileSync(schemesPath, "utf-8"));
      const matched = schemesData.filter((item: any) => {
        const text = `${item.name} ${item.description}`.toLowerCase();
        return keywords.some(kw => text.includes(kw));
      });
      if (matched.length > 0) {
        contextText += "Relevant Government Schemes:\n" + JSON.stringify(matched.slice(0, 3), null, 2) + "\n\n";
      }
    }

    return contextText;
  } catch (err) {
    console.error("RAG Error:", err);
    return "";
  }
}

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();
    
    if (!messages || !Array.isArray(messages)) {
      return new Response("Missing messages", { status: 400 });
    }

    const latestMessage = messages[messages.length - 1].content;
    const ragContext = getLocalRAGContext(latestMessage);

    const systemInstruction = `You are KisanNet AI, a trusted, highly knowledgeable agricultural expert serving farmers in India.
Your goal is to provide concise, practical, and highly accurate advice regarding crop diseases, pest management, market prices, and government schemes.
Keep your answers brief and readable. Use emojis where appropriate. If asked about a topic outside of agriculture, gently steer the conversation back.

${ragContext ? `Here is some strictly vetted context retrieved from the KisanNet Knowledge Base for the user's query. Use this to ground your answers:\n\n${ragContext}` : ""}`;

    // Convert OpenAI style messages to Gemini format
    const contents = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }]
    }));

    const ai = getAI();
    if (!ai) {
      return new Response("Missing GEMINI_API_KEY environment variable.", { status: 500 });
    }

    const responseStream = await ai.models.generateContentStream({
      model: "gemini-3.6-flash",
      contents: contents,
      config: {
        systemInstruction: systemInstruction,
        temperature: 0.3,
      }
    });

    const encoder = new TextEncoder();
    
    // Create a readable stream
    const stream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of responseStream) {
            controller.enqueue(encoder.encode(chunk.text));
          }
          controller.close();
        } catch (e) {
          controller.error(e);
        }
      }
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
      }
    });

  } catch (error: any) {
    console.error("AI Route Error:", error);
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
}
