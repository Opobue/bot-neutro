import { getConfig, Tier } from '../config';

export interface AudioUsage {
  total_ms: number;
  provider_llm: string;
}

export interface AudioResponse {
  transcript: string;
  reply_text: string;
  usage: AudioUsage;
  corr_id: string;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const callAudioEndpoint = async (
  file: File,
  tier: Tier,
): Promise<AudioResponse> => {
  const config = getConfig();
  const url = `${config.apiBaseUrl}/audio`;
  const formData = new FormData();
  formData.append('audio_file', file);

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
      'X-API-Key': config.apiKey,
      'x-munay-llm-tier': tier,
    },
  });

  if (!response.ok) {
    const message = response.status === 401
      ? 'API Key inválida o faltante'
      : response.status === 422
        ? 'Archivo de audio inválido o faltante'
        : 'Error al procesar el audio';
    throw new ApiError(message, response.status);
  }

  const data = (await response.json()) as AudioResponse;
  return data;
};
