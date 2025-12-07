import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { randomSeed } from 'k6';

randomSeed(new Date().getTime());

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'changeme';
const RATE = Number(__ENV.RPS || 5); // requests per second
const DURATION = __ENV.TEST_DURATION || '1m';
const VUS = Number(__ENV.VUS || Math.max(10, RATE));

export const options = {
  scenarios: {
    audio_constant_rps: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: VUS,
      maxVUs: Math.max(VUS, RATE * 2),
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1500'],
  },
};

const audioBytes = open('./sample_silence.wav', 'b');
const audioFile = http.file(audioBytes, 'sample_silence.wav', 'audio/wav');

const clientLatency = new Trend('audio_client_latency_ms');
const clientErrors = new Rate('audio_client_errors');

export default function () {
  const corrId = `k6-audio-${__VU}-${__ITER}-${Date.now()}`;

  const res = http.post(
    `${BASE_URL}/audio`,
    {
      // FastAPI espera el campo "audio_file" (UploadFile)
      audio_file: audioFile,
    },
    {
      headers: {
        'X-API-Key': API_KEY,
        'X-Correlation-Id': corrId,
      },
    },
  );

  clientLatency.add(res.timings.duration);
  clientErrors.add(res.status >= 400);

  check(res, {
    'status is success or rate-limited': (r) => r.status === 200 || r.status === 429,
  });
}
