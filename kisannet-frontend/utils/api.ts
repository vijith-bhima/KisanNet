// API Service for interacting with KisanNet Backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface JournalStatusResponse {
  id: string;
  is_fully_processed: boolean;
  transcription?: string;
  advice_text?: string;
  advice_source?: string;
  cost_benefit?: string;
  tts_prompt?: string;
  audio_base64?: string;
}

/**
 * Ingest audio (via Base64 JSON instead of FormData)
 * The backend supports /api/v1/pillar1/ingest-json
 */
export async function ingestAudioJson(audioBase64: string, languageCode: string = 'te-IN'): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/pillar1/ingest-json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      audio_base64: audioBase64,
      channel: 'BROWSER',
      language_code: languageCode,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to ingest audio: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Poll for journal processing status
 */
export async function pollJournalStatus(journalId: string): Promise<JournalStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/pillar1/journal-status/${journalId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch journal status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Converts a Blob to a base64 string
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // FileReader result looks like "data:audio/webm;base64,GkXf..."
      // We need to split and get just the base64 part for the backend
      const base64String = reader.result?.toString().split(',')[1];
      if (base64String) {
        resolve(base64String);
      } else {
        reject(new Error('Failed to convert Blob to Base64'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
