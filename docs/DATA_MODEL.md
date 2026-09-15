# Modelo de datos — EditorAgent

## 1. Entidades principales

### Project

Representa un espacio de trabajo local.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| name | string | Nombre visible |
| root_path | string | Carpeta de artefactos del proyecto |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |
| app_version | string | Trazabilidad |

### MediaRoot

Carpeta fuente añadida en modo sólo lectura.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK Project |
| path | string | Ruta normalizada |
| display_name | string | Etiqueta de UI |
| added_at | datetime | UTC |
| read_only_confirmed | boolean | Debe ser true |

### Clip

Representa un archivo fuente de vídeo.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK Project |
| media_root_id | UUID | FK MediaRoot |
| relative_path | string | Ruta relativa a MediaRoot |
| source_fingerprint | string | Tamaño + mtime + hash parcial/estrategia versionada |
| duration_seconds | float | Derivado de ffprobe |
| fps_num/fps_den | integer | Preservar racional |
| is_vfr | boolean/null | Si puede inferirse |
| width/height | integer | Resolución codificada |
| codec | string | Codec vídeo |
| pixel_format | string | p. ej. yuv420p10le |
| color_metadata_json | JSON | Datos relevantes |
| capture_time | datetime/null | Si disponible |
| ingest_status | enum | discovered/valid/unsupported/error |
| error_message | string/null | Seguro para UI |

### AnalysisRun

Ejecución versionada de un análisis con una configuración concreta.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK Project |
| profile_name | string | `cinematic_drone_v1`, etc. |
| config_json | JSON | Configuración completa |
| config_hash | string | Hash estable |
| analyzer_version | string | SemVer/git SHA |
| started_at/finished_at | datetime | UTC |
| status | enum | queued/running/completed/failed/cancelled |

### ClipAnalysis

Relación entre un clip y un AnalysisRun.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| analysis_run_id | UUID | FK |
| clip_id | UUID | FK |
| status | enum | Estado por clip |
| progress | float | 0..1 |
| diagnostics_json | JSON | Rendimiento, warnings, etc. |
| error_message | string/null | Error aislado |

### WindowMetric

Agregado temporal de señales. Para evitar tablas gigantes, se puede guardar en JSON/Parquet por `ClipAnalysis` y conservar en DB sólo referencia e índices.

| Campo | Tipo | Notas |
|---|---|---|
| clip_analysis_id | UUID | FK |
| start_seconds/end_seconds | float | Intervalo real |
| values_json | JSON | Métricas crudas y normalizadas |
| composite_score | float | 0..1 |

### Segment

Candidato o selección de usuario derivada de un clip y análisis.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| clip_id | UUID | FK |
| analysis_run_id | UUID/null | Null si creado manualmente |
| start_seconds/end_seconds | float | Rango no destructivo |
| overall_score | float/null | Score de análisis |
| metrics_json | JSON | Scores relevantes |
| reasons_json | JSON array | Explicaciones positivas |
| penalties_json | JSON array | Penalizaciones |
| status | enum | suggested/approved/rejected/manual |
| user_note | text/null | Nota libre |
| created_at/updated_at | datetime | UTC |

### Export

Registro de una exportación reproducible.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK |
| format | enum | csv/fcpxml/edl |
| destination_path | string | Ruta explícita |
| selection_query_json | JSON | Qué se exportó |
| created_at | datetime | UTC |
| status | enum | completed/failed |
| manifest_json | JSON | Segmentos + versiones exportadas |

### HumanLabel

Decisión humana estructurada utilizada para evaluación y futura personalización. No sustituye al
estado editorial de `Segment`.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK Project |
| clip_id | UUID | FK Clip |
| analysis_run_id | UUID/null | Ejecución que produjo las métricas observadas |
| segment_id | UUID/null | Segmento editorial relacionado, si existe |
| start_seconds/end_seconds | float | Intervalo etiquetado |
| utility_label | enum | usable/unusable/uncertain |
| shot_type | enum/null | traveling/orbit/hover/fpv_dynamic/etc. |
| motion_quality | enum/null | smooth/intentional_dynamic/abrupt/vibration/uncertain |
| rejection_reason | enum/null | blur/exposure/jerk/redundant/content/etc. |
| confidence | enum/null | high/medium/low |
| note | text/null | Contexto humano |
| annotator | string | Identidad local del anotador |
| created_at/updated_at | datetime | UTC |

### LabelingSession

Sesión de trabajo para medir progreso de adquisición de conocimiento.

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID | Clave primaria |
| project_id | UUID | FK Project |
| annotator | string | Usuario local |
| status | enum | active/completed/paused |
| clips_total/clips_completed | integer | Progreso de la sesión |
| labels_count | integer | Número de etiquetas guardadas |
| started_at/finished_at | datetime/null | UTC |

## 2. Invariantes

- `0 <= start_seconds < end_seconds <= clip.duration_seconds`.
- Ningún Segment modifica un Clip fuente.
- Todo Segment automático referencia un `AnalysisRun` válido.
- Un reanálisis nunca sobreescribe métricas históricas sin crear una nueva versión.
- Las rutas de exportación no pueden ser implícitamente una carpeta de originales.
- La eliminación de un proyecto nunca elimina fuentes externas.

## 3. Estados de segmento

```text
suggested → approved
suggested → rejected
suggested → manual (cuando el usuario ajusta rangos)
manual → approved | rejected
```

Conservar historial de decisiones si el coste de almacenamiento es razonable; como mínimo guardar `updated_at` y estado previo en un log de auditoría.
