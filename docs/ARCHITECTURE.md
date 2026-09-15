# Arquitectura técnica — EditorAgent

## 1. Principio rector

EditorAgent separa la ingestión, el análisis, el almacenamiento de resultados, las exportaciones y la interfaz. El pipeline debe poder ejecutarse por CLI/API sin depender de la UI, y la UI nunca debe contener lógica de visión por computador.

## 2. Arquitectura propuesta

```text
┌─────────────────────────────────────────────────────────────┐
│ React + TypeScript UI                                        │
│ Proyectos · Revisión · Player proxy · Filtros · Exportación  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/WebSocket local
┌───────────────────────────▼─────────────────────────────────┐
│ FastAPI local                                                │
│ API de proyecto, medios, análisis, selección y exportación   │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
┌───────────────▼──────────────┐  ┌─────────────▼─────────────┐
│ SQLite                        │  │ Job queue persistente      │
│ proyectos, clips, métricas,   │  │ cancelación, progreso,     │
│ segmentos, decisiones, logs   │  │ reintentos, workers        │
└──────────────────────────────┘  └─────────────┬─────────────┘
                                                  │
                              ┌───────────────────▼──────────────────┐
                              │ Workers de análisis en procesos       │
                              │ ffprobe · FFmpeg · OpenCV · modelos    │
                              └─────────┬───────────────┬────────────┘
                                        │               │
                ┌───────────────────────▼───┐     ┌─────▼────────────────────┐
                │ Originales: sólo lectura     │     │ Artefactos de proyecto        │
                │ rutas fuente externas       │     │ proxies, thumbnails, exports  │
                └────────────────────────────┘     └──────────────────────────┘
```

                ### Convención frontend

                La UI React seguirá Atomic Design cuando comience la siguiente iteración estructural:

                ```text
                frontend/src/
                ├── components/
                │   ├── atoms/
                │   ├── molecules/
                │   └── organisms/
                ├── pages/
                ├── hooks/
                ├── lib/
                │   └── api/
                ├── styles/
                │   ├── tokens.css
                │   └── modules/
                └── types/
                ```

                Los componentes visuales no accederán directamente a SQLite ni contendrán lógica de análisis.
                La comunicación pasará por `lib/api`, los tipos compartidos vivirán en `types` y los estilos
                se dividirán por módulo sólo cuando exista una frontera funcional clara. La pantalla inicial
                actual es un prototipo vertical y se reorganizará bajo esta estructura antes de ampliar la UI.

## 3. Estructura de repositorio inicial

```text
editoragent/
├── AGENTS.md
├── README.md
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── ANALYSIS_SPEC.md
│   ├── DATA_MODEL.md
│   ├── UX_SPEC.md
│   ├── EVALUATION.md
│   ├── SECURITY_PRIVACY.md
│   └── DECISIONS.md
├── apps/
│   └── desktop/                 # Tauri shell cuando corresponda
├── frontend/
│   ├── src/
│   └── package.json
├── backend/
│   ├── editoragent/
│   │   ├── api/
│   │   ├── domain/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── analyzers/
│   │   ├── exporters/
│   │   └── infrastructure/
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic/
├── fixtures/
│   ├── metadata/
│   └── expected/
├── scripts/
├── .github/workflows/
└── docker/                      # Sólo para desarrollo/CI, no requisito de usuario
```

## 4. Pipeline de procesamiento

### Paso 1: descubrimiento e inventario

- Enumerar archivos soportados de las carpetas fuente.
- Normalizar rutas de forma portable.
- Registrar tamaño, mtime y una huella ligera para detectar cambios sin hashear gigabytes innecesariamente.
- Ejecutar `ffprobe` con salida JSON.
- Validar que existe al menos un stream de vídeo legible.

### Paso 2: proxy y thumbnails

- Crear proxy configurable, por ejemplo 720p/1080p con codec ampliamente reproducible.
- Mantener relación de aspecto, rotación y audio si es útil para la revisión.
- Generar thumbnails cada N segundos y/o un filmstrip por segmento.
- Guardar metadatos de generación y evitar regenerar artefactos válidos.

### Paso 3: muestreo de señales

- Extraer frames o decodificar a una tasa de muestreo configurable.
- Para cada frame/ventana, medir nitidez, luminancia, clipping, congelación y movimiento.
- Mantener los datos crudos agregados por ventanas para permitir nuevos umbrales sin reprocesar todo cuando sea posible.

### Paso 4: scoring

- Normalizar métricas a rangos comparables `[0, 1]`.
- Calcular score técnico y sub-scores independientes.
- Aplicar perfiles de vuelo; no mezclar arbitrariamente FPV y cine.
- Conservar contribuciones y razones de cada score.

### Paso 5: construcción de segmentos

- Aplicar suavizado temporal.
- Usar hysteresis: umbral de entrada superior y umbral de salida inferior.
- Exigir duración mínima.
- Unir huecos pequeños si su calidad no cae de forma grave.
- Recortar handles configurables sin invadir los límites del clip.
- Eliminar segmentos redundantes o priorizar el mejor de grupos similares cuando esa función esté disponible.

### Paso 6: revisión y exportación

- Servir segmentos ordenados, filtros y artefactos visuales.
- Persistir decisiones del usuario sin destruir sugerencias originales.
- Crear exportaciones como operaciones explícitas, versionadas y registradas.

## 5. Concurrencia y rendimiento

- Un worker procesa un clip o una unidad acotada; no compartir estado mutable innecesario.
- Límite de paralelismo configurable según CPU, RAM y capacidad de decodificación.
- Toda tarea debe reportar estados: `queued`, `running`, `completed`, `failed`, `cancelled`.
- Los workers escriben checkpoints por fase para reanudar de forma segura.
- Los frames deben procesarse en streaming; no cargar clips enteros.
- Degradar con elegancia: si optical flow es demasiado caro, usar muestreo menor o una métrica básica y declarar la limitación.

## 6. Gestión de FFmpeg

- Localizar binarios de forma explícita y mostrar versión al iniciar diagnóstico.
- No interpolar strings de shell con rutas de usuario. Usar listas de argumentos y `subprocess` sin shell.
- Capturar stderr y almacenarlo como detalle técnico del error, no como único mensaje para el usuario.
- Especificar `-map`, codecs y color management de forma deliberada al crear proxies.
- Tratar VFR y timebases mediante timestamps derivados de ffprobe, no suponiendo FPS fijo.

## 7. Interfaces internas sugeridas

```python
class ClipAnalyzer(Protocol):
    name: str
    version: str

    def analyze(self, clip: Clip, config: AnalysisConfig) -> AnalysisResult:
        ...

class SegmentBuilder(Protocol):
    def build(self, windows: list[WindowScore], config: SegmentConfig) -> list[Segment]:
        ...

class Exporter(Protocol):
    format_name: str

    def export(self, project: Project, segments: list[Segment], destination: Path) -> ExportResult:
        ...
```

## 8. Errores y observabilidad local

- Diferenciar: archivo no soportado, vídeo corrupto, codec no disponible, falta de permisos, espacio insuficiente, proceso cancelado y fallo interno.
- Guardar logs por proyecto y por job, con rotación.
- Ofrecer una pantalla de diagnóstico exportable que incluya versiones de aplicación, FFmpeg, SO, GPU opcional y últimos errores, siempre sin subirlo automáticamente.

## 9. Decisiones pendientes

- Motor concreto de cola local: SQLite-backed queue propia, Dramatiq/RQ local o proceso supervisor.
- Estrategia de almacenamiento de series temporales de métricas: SQLite agregada, Parquet/JSON por clip o híbrido.

## 10. Workspace unificado de selección y etiquetado

La UI tendrá un workspace principal orientado a una sesión de trabajo humana:

```text
inventario de clips -> reproductor/timeline -> segmentos del clip -> decisión y etiquetas -> exportación
                                                      |
                                                      v
                                             dataset de conocimiento
```

La API seguirá siendo la frontera entre React y SQLite. El frontend no leerá artefactos ni bases de
datos directamente. La revisión editorial seguirá usando `Segment`; las etiquetas destinadas a
evaluación o aprendizaje se persistirán en entidades propias relacionadas con `Clip`, `Segment` y
`AnalysisRun`.

La exportación editorial y la exportación de conocimiento serán salidas independientes. FCPXML no
debe convertirse en el formato de entrenamiento, y un dataset no debe modificar el estado de
aprobación de los segmentos.

El backoffice técnico podrá crear nuevas configuraciones y ejecuciones, pero nunca sobrescribirá
las métricas históricas ni los resultados de una ejecución anterior.
- Formato final de integración con DaVinci Resolve y validación de FCPXML.
- Criterio para activar modelos ML opcionales.
