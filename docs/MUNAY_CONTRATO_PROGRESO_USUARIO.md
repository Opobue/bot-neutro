# Munay: Contrato de Progreso de Usuario

Este contrato describe cómo Munay modela y consulta el progreso diario del usuario, enlazando eventos de audio procesados por el Bot Neutro.

## Entidad `munay_progress_daily`

| Campo                | Descripción                                      |
| -------------------- | ------------------------------------------------ |
| `user_id`            | Identificador interno de usuario en Munay.       |
| `date`               | Fecha (YYYY-MM-DD).                              |
| `acts_of_self_care`  | Conteo de acciones de autocuidado.               |
| `journal_entries`    | Conteo de entradas de diario (`journal_entry`).  |
| `coach_interactions` | Conteo de interacciones de coaching de hábitos.  |
| `insights`           | Conteo de insights (`insight`).                  |
| `crisis_flags`       | Conteo de flags de crisis (`crisis_flag`).       |
| `streak_days`        | Racha de días consecutivos con actividad.        |
| `last_updated_at`    | Timestamp de última actualización.               |

## Relación con eventos y sesiones de audio

Cada fila de `munay_progress_daily` se alimenta a partir de `munay_event`, y cada evento referencia el `audio_session` correspondiente proveniente del Bot Neutro.

## Endpoint de consulta

- `GET /munay/users/{user_id}/progress`
- Respuesta JSON de ejemplo:

```json
{
  "user_id": "user-123",
  "date": "2024-06-01",
  "acts_of_self_care": 2,
  "journal_entries": 1,
  "coach_interactions": 1,
  "insights": 1,
  "crisis_flags": 0,
  "streak_days": 5,
  "last_updated_at": "2024-06-01T18:30:00Z"
}
```

Todas las respuestas incluyen `X-Correlation-Id` y respetan los headers estándar del Bot Neutro.
