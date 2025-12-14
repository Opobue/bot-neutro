# CLIENTE_OFICIAL_MUNAY_TECNICO_V1

## Objetivo
Cliente web mínimo para consumir el endpoint `/audio` siguiendo los contratos:
- `docs/CONTRATO_API_PUBLICA_V1.md`
- `docs/CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md`
- `docs/UX_CLIENTE_OFICIAL_MUNAY_V1.md`
- `docs/02_ESTADO_Y_NORTE.md`

## Stack elegido
- React + TypeScript + Vite (SPA simple)
- Ubicación del código: `clients/munay-dashboard/`

## Estructura de carpetas
```
clients/munay-dashboard/
├─ index.html
├─ package.json
├─ tsconfig.json
├─ vite.config.ts
├─ .env.example
└─ src/
   ├─ main.tsx
   ├─ App.tsx
   ├─ styles.css
   ├─ config.ts
   ├─ api/client.ts
   └─ components/
      ├─ AudioUploader.tsx
      └─ ResultPanel.tsx
```

## Variables de entorno
- `VITE_API_BASE_URL`: URL base del backend (ej. `http://127.0.0.1:8000`).
- `VITE_API_KEY`: API Key que se enviará en `X-API-Key`.
- `VITE_DEFAULT_TIER`: tier por defecto (`freemium` o `premium`).

Crear `clients/munay-dashboard/.env.local` copiando de `.env.example` y ajustando valores.

## Comandos de desarrollo
Desde `clients/munay-dashboard/`:
- `npm install` – instala dependencias.
- `npm run dev` – levanta el dashboard en modo desarrollo.
- `npm run build` – verifica que compile para producción.
- `npm run preview` – sirve el build generado.

## Flujo de uso
1. Levantar backend local: `uvicorn bot_neutro.api:app --reload`.
2. Configurar `.env.local` con `VITE_API_BASE_URL`, `VITE_API_KEY`, `VITE_DEFAULT_TIER`.
3. Ejecutar `npm run dev` y abrir el puerto que indique Vite.
4. Seleccionar un archivo de audio (WAV/MP3 recomendado), elegir tier y presionar “Enviar a /audio”.

La consola del navegador loguea: `corr_id`, `usage.total_ms`, `usage.provider_llm`.

## Casos de prueba manual (checklist)
- Caso 1: `freemium`, audio válido, API Key correcta → 200 OK, se visualizan `transcript`, `reply_text`, `usage.total_ms`, `usage.provider_llm`, `corr_id`.
- Caso 2: API Key incorrecta → error 401 claro en UI.
- Caso 3: sin archivo → error 422 claro en UI.
- Caso 4: falta de crédito / modo stub → UI funcional, badge “Modo stub activo”, `provider_llm` con `stub`.

## Observabilidad mínima
- Consola del navegador registra `corr_id`, `usage.total_ms`, `usage.provider_llm` por cada respuesta exitosa.

## Consideraciones de seguridad
- `VITE_API_KEY` se incrusta en el bundle del frontend. Este cliente está pensado para uso local o entornos controlados.
- Para distribuciones públicas se recomienda colocar un backend proxy que firme o valide peticiones en lugar de exponer una API Key estática en el navegador.
