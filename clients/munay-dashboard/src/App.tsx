import { useEffect, useState } from 'react';
import AudioUploader from './components/AudioUploader';
import ResultPanel from './components/ResultPanel';
import { callAudioEndpoint, AudioResponse, ApiError } from './api/client';
import { ClientConfig, getConfig, Tier } from './config';

const App = () => {
  const [configError, setConfigError] = useState<string | null>(null);
  const [config, setConfig] = useState<ClientConfig | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [tier, setTier] = useState<Tier>('freemium');
  const [result, setResult] = useState<AudioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  useEffect(() => {
    try {
      const resolvedConfig = getConfig();
      setConfig(resolvedConfig);
      setTier(resolvedConfig.defaultTier);
    } catch (e) {
      setConfigError((e as Error).message);
    }
  }, []);

  const handleSubmit = async () => {
    if (!file) {
      setError('Selecciona un archivo de audio antes de enviar');
      setStatus('error');
      return;
    }

    setStatus('sending');
    setError(null);

    try {
      const response = await callAudioEndpoint(file, tier);
      setResult(response);
      setStatus('success');
      console.info('[munay-dashboard] corr_id', response.corr_id);
      console.info('[munay-dashboard] usage.total_ms', response.usage.total_ms);
      console.info('[munay-dashboard] usage.provider_llm', response.usage.provider_llm);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setStatus('error');
        return;
      }
      setError('Error inesperado al llamar a /audio');
      setStatus('error');
    }
  };

  return (
    <div className="container">
      <h1>Cliente oficial Munay - /audio</h1>
      <p className="subtitle">
        Dashboard mínimo para probar el endpoint /audio según contratos públicos.
      </p>

      {configError && (
        <div className="card" style={{ borderColor: '#f87171', background: '#fef2f2' }}>
          <h2 style={{ color: '#b91c1c', marginBottom: 8 }}>Error de configuración</h2>
          <p style={{ marginBottom: 6 }}>{configError}</p>
          <p style={{ color: '#6b7280', fontSize: 13 }}>
            Revisa tu archivo <code>.env.local</code> en <code>clients/munay-dashboard</code>.
          </p>
        </div>
      )}

      {!config && !configError && <div className="card">Cargando configuración...</div>}

      {config && !configError && (
        <>
          <AudioUploader
            selectedTier={tier}
            onTierChange={setTier}
            onFileSelected={(selectedFile) => {
              setFile(selectedFile);
            }}
            fileName={file?.name ?? null}
            onSubmit={handleSubmit}
            disabled={status === 'sending'}
          />

          <ResultPanel result={result} error={error} status={status} />

          <div className="card" style={{ marginTop: 20 }}>
            <h3>Config actual</h3>
            <div className="code-block">
              <div>API_BASE_URL: {config.apiBaseUrl}</div>
              <div>DEFAULT_TIER: {config.defaultTier}</div>
            </div>
            <p style={{ color: '#6b7280', fontSize: 13 }}>
              La API Key se lee desde variables de entorno (VITE_API_KEY) y no se expone en la UI.
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default App;
