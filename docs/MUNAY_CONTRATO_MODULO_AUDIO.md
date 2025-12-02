# Munay: Contrato de Consumo del Módulo de Audio del Bot Neutro

Este documento describe cómo el cliente Munay consume el endpoint `/audio` del Bot Neutro.

## Petición

- **Método**: `POST /audio`
- **Contenido**: `multipart/form-data`
  - Campo obligatorio `file`: archivo de audio
- **Headers obligatorios**:
  - `X-API-Key`
  - `X-Correlation-Id`
  - `x-munay-user-id`
  - `x-munay-context`

## Contextos permitidos

`x-munay-context` admite los valores:

- `diario_emocional`
- `coach_habitos`
- `reflexion_general`

## Mapeo a eventos Munay

El consumo de `/audio` genera un `munay_event` con los siguientes mapeos:

- `diario_emocional` → `journal_entry`
- `coach_habitos` → `habit_coaching`
- `reflexion_general` → `insight`
- El sistema puede marcar `crisis_flag` si el pipeline detecta alerta.

Cada evento se enriquece con `audio_session_id` retornado por el Bot Neutro.
