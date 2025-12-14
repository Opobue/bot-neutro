import { useRef } from 'react';
import { Tier } from '../config';

interface Props {
  selectedTier: Tier;
  onTierChange: (tier: Tier) => void;
  onFileSelected: (file: File | null) => void;
  fileName?: string | null;
  onSubmit: () => void;
  disabled: boolean;
}

const AudioUploader = ({ selectedTier, onTierChange, onFileSelected, onSubmit, disabled, fileName }: Props) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    onFileSelected(file);
  };

  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="card">
      <h2>Subir audio</h2>
      <p className="subtitle">Selecciona un archivo WAV/MP3 y define el tier de LLM.</p>

      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <span className="label">Archivo de audio</span>
          <div className="row" style={{ gap: 8 }}>
            <button type="button" className="button" onClick={handleChooseFile} disabled={disabled}>
              Elegir archivo
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              data-testid="file-input"
            />
          </div>
          <div style={{ marginTop: 6, fontSize: 13, color: '#374151' }}>
            {fileName ? `Archivo seleccionado: ${fileName}` : 'Ningún archivo seleccionado'}
          </div>
          <small style={{ color: '#6b7280' }}>Recomendado: WAV con audio claro.</small>
        </div>
        <div>
          <span className="label">Tier LLM</span>
          <select
            className="select"
            value={selectedTier}
            onChange={(e) => onTierChange(e.target.value as Tier)}
            disabled={disabled}
          >
            <option value="freemium">freemium (por defecto)</option>
            <option value="premium">premium</option>
          </select>
        </div>
      </div>

      <button type="button" className="button" onClick={onSubmit} disabled={disabled}>
        Enviar a /audio
      </button>
    </div>
  );
};

export default AudioUploader;
