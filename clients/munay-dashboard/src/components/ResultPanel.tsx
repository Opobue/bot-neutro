import { AudioResponse } from '../api/client';

interface Props {
  result: AudioResponse | null;
  error: string | null;
  status: 'idle' | 'sending' | 'success' | 'error';
}

const ResultPanel = ({ result, error, status }: Props) => {
  if (status === 'idle') {
    return null;
  }

  if (status === 'sending') {
    return <div className="status">Enviando audio…</div>;
  }

  if (status === 'error') {
    return <div className="status error">{error}</div>;
  }

  if (!result) {
    return null;
  }

  const isStub = result.usage.provider_llm.toLowerCase().includes('stub');

  return (
    <div className="panel">
      <div className="row" style={{ alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Resultado</h3>
        {isStub && <span className="badge">Modo stub activo (respuesta de prueba)</span>}
      </div>
      <div className="result-grid">
        <div>
          <span className="label">Transcript</span>
          <div className="card" style={{ padding: 12 }}>{result.transcript}</div>
        </div>
        <div>
          <span className="label">Reply Text</span>
          <div className="card" style={{ padding: 12 }}>{result.reply_text}</div>
        </div>
        <div>
          <span className="label">Tiempo total (ms)</span>
          <div className="card" style={{ padding: 12 }}>{result.usage.total_ms}</div>
        </div>
        <div>
          <span className="label">Provider LLM</span>
          <div className="card" style={{ padding: 12 }}>{result.usage.provider_llm}</div>
        </div>
        <div>
          <span className="label">corr_id</span>
          <div className="card" style={{ padding: 12, wordBreak: 'break-all' }}>{result.corr_id}</div>
        </div>
      </div>
    </div>
  );
};

export default ResultPanel;
