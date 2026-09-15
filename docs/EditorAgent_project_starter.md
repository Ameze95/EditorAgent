# EditorAgent — Paquete inicial de producto y desarrollo

Este documento contiene los archivos Markdown iniciales para arrancar EditorAgent. Crea cada bloque como un archivo independiente respetando el nombre indicado.

---

## `README.md`

# EditorAgent

**EditorAgent** es una herramienta local-first de análisis, selección y recorte asistido de metraje, inicialmente optimizada para vídeo de drones. Convierte carpetas de clips brutos en una preselección revisable de intervalos utilizables: tomas nítidas, técnicamente correctas, estables o con movimiento intencional y suficientemente largas para editar.

No pretende sustituir a un editor. Su objetivo es reducir el tiempo de visionado, descarte y marcado inicial, manteniendo al usuario en control de cada decisión creativa.

## Problema

Después de una sesión de vuelo es habitual acumular decenas o cientos de clips. El editor debe localizar manualmente:

- Despegues y aterrizajes que deben descartarse.
- Correcciones bruscas de sticks o de gimbal.
- Trepidación, vibración, desenfoque y pérdida de foco.
- Exposición rota, highlights quemados o negros aplastados.
- Fragmentos de movimiento fluido y continuidad suficiente.
- Repeticiones de una misma pasada o encuadre.

El visionado completo consume tiempo y la mayor parte de los clips no llega al corte final. EditorAgent automatiza una **preselección explicable**, no una decisión creativa opaca.

## Propuesta de valor

1. Analizar localmente una carpeta de vídeo sin subir los originales.
2. Dividir cada clip en ventanas temporales y puntuarlas.
3. Proponer intervalos candidatos con puntuación y motivos verificables.
4. Permitir aprobar, rechazar, ajustar y etiquetar segmentos rápidamente.
5. Exportar el resultado para edición profesional: CSV, EDL/FCPXML y, posteriormente, marcadores compatibles con DaVinci Resolve y Premiere Pro.
6. Aprender de las decisiones de cada usuario mediante perfiles y feedback, sin exigir entrenamiento cloud.

## Principios del producto

- **Local-first:** los originales, proxies y análisis permanecen en el equipo salvo acción explícita del usuario.
- **No destructivo:** jamás modifica el archivo fuente.
- **Human-in-the-loop:** toda selección automática es una recomendación revisable.
- **Explicable:** cada score debe indicar qué señales lo han elevado o penalizado.
- **Progresivo:** entregar valor con heurísticas sencillas antes de introducir modelos pesados.
- **Reproducible:** el análisis debe guardar versión, parámetros, fecha y resultados por proyecto.
- **Profesional:** las salidas deben encajar en flujos existentes, no encerrar al usuario en un editor propio.

## Usuario inicial

- Pilotos de dron DJI/cinemático y FPV que generan mucho material por sesión.
- Videógrafos de eventos, inmobiliario, turismo, exterior y marcas.
- Creadores que editan con DaVinci Resolve, Premiere Pro, Final Cut Pro o herramientas similares.
- Técnicos audiovisuales y estudios que necesitan ingestión y selección rápida de grandes volúmenes de material.

## No es, por ahora

- Un sustituto de DaVinci Resolve/Premiere.
- Un estabilizador o corrector de color automático como función central.
- Un generador de reels con música como prioridad inicial.
- Un sistema cloud obligatorio.
- Un clasificador perfecto de valor narrativo o gusto estético.

## Resultado ideal del MVP

El usuario elige una carpeta, ejecuta un análisis y recibe en pocos minutos:

- Una lista ordenada de segmentos recomendados.
- Inicio, fin, duración y score de cada segmento.
- Razones de aceptación/rechazo.
- Thumbnails o filmstrip para revisar visualmente.
- Exportación CSV y FCPXML/EDL.

## Estado

Fase: definición y prototipo técnico.

Consulta `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` y `AGENTS.md` antes de implementar.

---

## `AGENTS.md`

# Instrucciones maestras para agentes — EditorAgent

## Rol

Actúa como un equipo senior de producto y desarrollo para **EditorAgent**, una aplicación local-first que analiza vídeo de dron y propone subclips utilizables para edición. Combina criterio de ingeniería de vídeo, visión por computador, UX profesional y arquitectura de software mantenible.

Tu misión no es producir una demo engañosa: es avanzar de forma incremental hacia un producto que funcione con metraje real, archivos grandes y flujos profesionales.

## Objetivo principal

Construir una aplicación capaz de tomar una carpeta de clips de vídeo, detectar y puntuar intervalos candidatos a edición y permitir que el usuario los revise y exporte sin alterar los originales.

La definición operativa inicial de un segmento «utilizable» es:

- Tiene una duración mínima configurable.
- Tiene nitidez suficiente durante la mayor parte del intervalo.
- No contiene sobreexposición o subexposición extrema sostenida.
- No contiene movimientos bruscos no intencionales, vibración o cambios repentinos de dirección/gimbal según umbrales configurables.
- Mantiene un movimiento de cámara coherente o estable.
- No pertenece a una zona marcada como despegue, aterrizaje, calibración o error, cuando dichas señales sean detectables.
- No es redundante frente a una toma equivalente que recibe mayor puntuación.

Esto es una definición técnica inicial, no una verdad estética. La interfaz debe dejar clara la incertidumbre y permitir corrección humana.

## Jerarquía de prioridades

Cuando existan compromisos, prioriza en este orden:

1. Integridad de los originales y seguridad del proyecto.
2. Resultados correctos, reproducibles y explicables.
3. Flujo de revisión rápido y útil para un editor humano.
4. Rendimiento razonable con material 4K/HEVC.
5. Arquitectura simple, modular y testeable.
6. Funciones de IA avanzadas y estética subjetiva.
7. Apariencia visual o funciones de marketing.

## Reglas no negociables

- No modifiques, muevas ni borres los archivos originales.
- Trabaja mediante lectura, proxies y metadatos. Todo resultado debe vivir en una carpeta de proyecto separada.
- No implementes inferencias pesadas en el hilo principal de la interfaz.
- No simules que una métrica técnica equivale a juicio editorial definitivo.
- No uses servicios cloud sin consentimiento explícito y granular del usuario.
- No incluyas telemetría por defecto.
- No exportes ni recomprimas originales a menos que el usuario lo solicite explícitamente.
- No codifiques rutas absolutas, parámetros mágicos o dependencias de una GPU concreta.
- No avances a una fase de ML compleja si las heurísticas, los tests y la exportación básica aún fallan.
- Mantén compatibilidad inicial con Windows; diseña para que macOS/Linux sean posibles después.

## Método de trabajo obligatorio

Para cada tarea:

1. Lee `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` y el código afectado.
2. Explica brevemente qué vas a cambiar, qué supuestos haces y cómo lo verificarás.
3. Divide cambios grandes en entregables verticales y comprobables.
4. Implementa la solución mínima completa, no una maqueta superficial.
5. Añade o actualiza tests cuando la lógica lo permita.
6. Ejecuta formateo, lint, chequeo de tipos y tests relevantes.
7. Documenta parámetros, formatos de entrada/salida y limitaciones.
8. Si falta una decisión de producto que cambie arquitectura, detente y formula preguntas concretas en lugar de inventar una respuesta.

## Estilo de ingeniería

- Prefiere funciones pequeñas, deterministas y con tipos claros.
- Separa dominio, infraestructura, procesamiento y UI.
- Modela intervalos usando segundos como `float` internamente; conserva también timestamps de frame cuando sea necesario.
- Siempre conserva la procedencia: clip fuente, hash/identificador, parámetros, versión del analizador y timestamp de análisis.
- Diseña jobs reanudables, cancelables y tolerantes a fallos por clip.
- Procesa vídeo por muestreo y streaming; evita cargar vídeos enteros en RAM.
- Genera proxies de baja resolución para análisis/UI cuando eso reduzca coste sin comprometer el objetivo.
- Trata HEVC, VFR, HDR, rotaciones y metadatos como casos reales, no excepciones improbables.
- Los resultados de cada métrica deben incluir valor, rango/normalización, umbral aplicado y razón legible por humanos.

## Decisiones técnicas base

Hasta que exista una razón probada para cambiarlas:

| Área | Decisión inicial |
|---|---|
| Runtime de análisis | Python 3.12+ |
| Procesamiento multimedia | FFmpeg y ffprobe mediante subprocess seguro |
| Visión por computador | OpenCV |
| API local | FastAPI |
| Persistencia | SQLite mediante SQLModel o SQLAlchemy |
| Frontend | React + TypeScript + Vite |
| Escritorio | Tauri, si se requiere empaquetado nativo; durante desarrollo puede funcionar como web local |
| Gestión de tareas | Cola local persistente y workers de procesos separados |
| Pruebas Python | pytest |
| Pruebas frontend | Vitest + Testing Library |
| Calidad | Ruff, mypy/pyright, ESLint, Prettier |
| Exportación inicial | CSV y FCPXML; EDL cuando los requisitos de timecode estén bien resueltos |

No conviertas esta tabla en dogma: propone cambios sólo con una justificación concreta de coste, fiabilidad, licencia y compatibilidad.

## Contrato de salida del análisis

Cada segmento propuesto debe tener como mínimo:

```json
{
  "id": "uuid",
  "clip_id": "uuid",
  "source_path": "ruta_relativa/al/original.mov",
  "start_seconds": 12.4,
  "end_seconds": 21.9,
  "duration_seconds": 9.5,
  "overall_score": 0.84,
  "status": "suggested",
  "metrics": {
    "sharpness": 0.91,
    "exposure": 0.84,
    "motion_smoothness": 0.82,
    "stability": 0.76,
    "technical_quality": 0.85,
    "aesthetic_score": null
  },
  "reasons": [
    "Movimiento de cámara consistente",
    "Nitidez alta",
    "Sin clipping de luces significativo"
  ],
  "penalties": [
    "Ligera corrección de gimbal hacia el final"
  ],
  "analysis_version": "0.1.0",
  "parameters_hash": "sha256..."
}
```

Los nombres pueden evolucionar, pero no se debe perder explicabilidad ni trazabilidad.

## Criterio de aceptación mínimo por entrega

Una funcionalidad está terminada sólo si:

- Tiene una ruta de uso real desde la UI o CLI.
- No daña el material original.
- Maneja errores de manera comprensible.
- Produce un resultado verificable con datos de prueba.
- Tiene documentación suficiente para que otro desarrollador la ejecute.
- No rompe los tests existentes.

## Preguntas que debes plantear cuando bloqueen diseño

Formula las preguntas en grupos pequeños y con recomendaciones. Ejemplos:

- ¿La prioridad inicial es dron cinemático, FPV, inmobiliario o eventos? Esto modifica la definición de movimiento bueno.
- ¿Qué editor de destino debe ser de primera clase: DaVinci Resolve, Premiere o Final Cut?
- ¿Debe funcionar totalmente sin GPU o se puede ofrecer aceleración opcional CUDA/Apple Silicon?
- ¿El usuario prefiere subclips físicos, XML/EDL/CSV, o las tres salidas?
- ¿Qué presupuesto de tiempo por hora de vídeo es aceptable en CPU y en GPU?
- ¿Los originales suelen ser H.264/H.265, 4K, 10-bit, HDR, VFR o DJI D-Log?

## Definición de éxito del MVP

Un usuario puede analizar al menos 20 clips reales, revisar los segmentos sugeridos con thumbnails, aprobar/rechazar rápidamente y exportar una selección importable o utilizable en su NLE. El sistema debe ahorrar tiempo de selección aun si sus recomendaciones no son perfectas.

---

## `docs/PRD.md`

# PRD — EditorAgent

## 1. Resumen

EditorAgent es un asistente de ingestión y selección de vídeo local-first. Analiza clips de dron y, posteriormente, otros tipos de material audiovisual para localizar intervalos técnicamente utilizables y presentarlos como una preselección editable.

La aplicación no toma el control del montaje narrativo. Reduce trabajo repetitivo: detectar tramos borrosos, vibración, exposición deficiente, arranques/paradas, correcciones bruscas y repeticiones.

## 2. Problema de usuario

Un creador puede grabar entre 30 minutos y varias horas de material para obtener pocos minutos válidos. La selección manual requiere reproducir cada clip, marcar puntos de entrada/salida y recordar tomas similares. Esto es lento y hace que material potencialmente bueno se pierda.

Las funciones existentes de auto-montaje suelen optimizar un vídeo final de redes, no un flujo de selección profesional y no explican suficientemente por qué descartaron una toma.

## 3. Jobs to be done

- Cuando termino una sesión de dron, quiero localizar rápidamente las partes limpias y fluidas para empezar a editar sin revisar todo el metraje a velocidad normal.
- Cuando tengo varias pasadas similares, quiero comparar y conservar la mejor según estabilidad, nitidez y composición básica.
- Cuando una sugerencia automática es incorrecta, quiero corregirla en pocos segundos y que el sistema tenga en cuenta mi criterio en análisis futuros.
- Cuando uso DaVinci Resolve/Premiere, quiero recibir una selección que respete mis originales y pueda importarse o consultarse sin reconstruirla a mano.

## 4. Personas

### Persona primaria: creador/piloto técnico

Graba con DJI u otros drones, entrega contenidos a clientes o proyectos propios y trabaja con 4K/HEVC. Tiene criterio de imagen, no quiere subir brutos privados y acepta herramientas técnicas si el ahorro de tiempo es tangible.

### Persona secundaria: editor audiovisual

Recibe mucho material de operadores diferentes. Necesita una bandeja de selects trazable, con motivos y una exportación compatible con el NLE.

## 5. Alcance MVP

### Incluido

- Crear y abrir un proyecto local.
- Añadir una o varias carpetas fuente en modo sólo lectura.
- Inventariar clips mediante ffprobe: codec, resolución, FPS, duración, timecode, orientación, fecha y metadatos disponibles.
- Generar proxies y thumbnails opcionales.
- Analizar ventanas temporales con heurísticas de calidad técnica.
- Proponer segmentos de duración mínima configurable.
- Mostrar lista/filmstrip de segmentos con score y motivos.
- Reproducir proxy y ajustar in/out manualmente.
- Aprobar, rechazar y etiquetar segmentos.
- Exportar CSV con rutas, intervalos y scores.
- Exportar FCPXML de selección, documentando compatibilidad validada.
- Guardar todos los parámetros y decisiones en SQLite.
- Cancelar y reanudar análisis por proyecto.

### Fuera del MVP

- Montaje automático final con música.
- Edición multicámara.
- Reconocimiento de personas/vehículos como requisito.
- Corrección de color automática destructiva.
- Estabilización aplicada al vídeo.
- Colaboración cloud o multiusuario.
- Entrenar un modelo personalizado desde la UI.
- Soporte garantizado para todos los códecs profesionales.

## 6. Requisitos funcionales

### RF-01: Proyecto

El usuario crea un proyecto con nombre y ubicación. La aplicación crea su propia estructura sin modificar las carpetas de medios.

### RF-02: Ingestión

El usuario selecciona una o varias carpetas. EditorAgent descubre extensiones configurables (`.mp4`, `.mov`, `.mkv`, `.mxf` inicialmente), ignora archivos no soportados y registra errores por archivo.

### RF-03: Metadatos

Por cada clip, registra al menos ruta, tamaño, modificación, duración, fps, resolución, codec, pixel format, color space, orientación y timecode si existen.

### RF-04: Análisis técnico

El sistema muestrea cada clip a una frecuencia configurable y calcula por ventana:

- Nitidez/desenfoque.
- Exposición y clipping aproximado.
- Movimiento global y consistencia temporal.
- Estabilidad/variación de movimiento.
- Frames negros, congelados o corruptos cuando se detecten.

### RF-05: Segmentación

El sistema convierte las puntuaciones por ventana en segmentos candidatos. Debe respetar duración mínima, hysteresis, uniones de huecos breves y handles configurables.

### RF-06: Explicación

Cada segmento presenta score global, duración, métricas principales, razones y penalizaciones. Nunca muestra una recomendación sin indicar al menos una señal de soporte o incertidumbre.

### RF-07: Revisión

El usuario puede filtrar, ordenar, reproducir, aprobar, rechazar, ajustar inicio/fin y añadir etiquetas/notas.

### RF-08: Exportación

El usuario exporta las selecciones aprobadas o sugeridas según filtro. El CSV debe ser siempre el formato de referencia legible. Las exportaciones no cambian los originales.

### RF-09: Reanálisis

El usuario puede relanzar el análisis al cambiar parámetros; las ejecuciones deben coexistir o quedar versionadas para permitir comparación y rollback.

## 7. Requisitos no funcionales

- Windows 11 es plataforma prioritaria.
- Debe funcionar sólo con CPU; GPU es aceleración opcional, no dependencia para MVP.
- Debe manejar interrupciones, clips corruptos y falta de espacio con mensajes accionables.
- Debe operar de forma local sin crear cuentas.
- Debe poder procesar al menos 20 clips 4K de duración moderada sin bloquear la UI.
- No se promete tiempo exacto hasta medir datasets representativos; la UI debe mostrar progreso por clip, ETA aproximada y fase actual.
- Las dependencias deben ser compatibles con uso comercial o estar claramente aisladas/detectables por licencia.

## 8. Métricas de éxito

### Métricas de producto

- Tiempo de selección manual ahorrado por proyecto.
- Porcentaje de segmentos sugeridos que el usuario aprueba.
- Porcentaje de segmentos aprobados que aparecen entre los primeros resultados ordenados por score.
- Tiempo medio hasta la primera selección revisable.
- Número de correcciones manuales por minuto de material.

### Métricas de calidad inicial

- No generar segmentos fuera de duración del clip.
- No perder trazabilidad de ruta, intervalo y parámetros.
- No modificar nunca un original.
- Detectar y penalizar de forma consistente casos controlados de blur, clipping y cámara errática.

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| La noción de toma buena es subjetiva | Separar calidad técnica de score estético; feedback y perfiles por tipo de vuelo |
| Procesamiento lento en 4K HEVC | Proxies, muestreo adaptativo, jobs en background y aceleración opcional |
| Vídeo HDR/log distorsiona métricas de exposición | Detectar metadatos de color; etiquetar incertidumbre; calibrar por perfil |
| FPV se confunde con movimiento malo | Perfiles diferenciados: cine, FPV, órbita, seguimiento; no usar una métrica única |
| XML/EDL varía entre NLEs | Empezar por CSV, crear fixtures y validar exportación en software real |
| Modelos de IA pesan mucho o tienen licencias restrictivas | Heurísticas como base; modelos opcionales, versionados y con revisión de licencia |

## 10. Preguntas abiertas

- ¿Qué NLE debe recibir soporte de exportación prioritario?
- ¿Qué drones, cámaras, códecs y perfiles de color representan el 80% del material inicial?
- ¿La aplicación se venderá como licencia local, suscripción, freemium o herramienta interna en la primera fase?
- ¿Qué nivel de privacidad se quiere garantizar y comunicar comercialmente?
- ¿Se aceptan modelos descargables opcionales o debe existir un modo portable/offline completo?

---

## `docs/ARCHITECTURE.md`

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
                              ┌───────────────────▼──────────────────┐n                              │ Workers de análisis en procesos         │
                              │ ffprobe · FFmpeg · OpenCV · modelos    │
                              └─────────┬───────────────┬────────────┘
                                        │               │
                ┌───────────────────────▼───┐     ┌─────▼────────────────────┐n                │ Originales: sólo lectura     │     │ Artefactos de proyecto        │
                │ rutas fuente externas       │     │ proxies, thumbnails, exports  │
                └────────────────────────────┘     └──────────────────────────┘
```

Nota de implementación: corregir cualquier carácter accidental `n` en el diagrama si se copia a una herramienta que lo muestre literalmente; el diagrama representa sólo conexiones verticales/horizontales.

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
- Formato final de integración con DaVinci Resolve y validación de FCPXML.
- Criterio para activar modelos ML opcionales.

---

## `docs/ANALYSIS_SPEC.md`

# Especificación de análisis — EditorAgent

## 1. Objetivo

Producir una puntuación técnica temporal para cada clip y convertirla en segmentos candidatos. El sistema debe distinguir entre movimiento alto pero controlado y movimiento errático, especialmente para no penalizar injustamente tomas FPV intencionales.

## 2. Unidad temporal

- Analizar por ventanas de 2 a 4 segundos con solapamiento inicial del 50%.
- Muestrear entre 2 y 8 FPS para las heurísticas básicas, configurable según resolución/rendimiento.
- Mantener timestamps reales por frame cuando sea posible, especialmente con vídeo VFR.
- Empezar con configuración conservadora y medible antes de aplicar análisis frame a frame costoso.

## 3. Métricas MVP

### 3.1 Nitidez

Señal base: varianza del Laplaciano sobre luminancia o imagen redimensionada. Complementar con percentiles dentro de una ventana, no sólo promedio.

Objetivo:

- Penalizar desenfoque sostenido, vibración y foco claramente fallido.
- Evitar descartar una toma por un único frame blando.

Advertencias:

- Niebla, bokeh, texturas pobres, noche y cielos lisos pueden producir scores bajos sin ser una toma defectuosa.
- La métrica se debe normalizar por clip o por perfil de cámara con cuidado; no aplicar un umbral universal ciego.

### 3.2 Exposición y clipping

Calcular sobre luminancia:

- Proporción de píxeles próximos a negro.
- Proporción de píxeles próximos a blanco.
- Percentiles de luminancia y rango dinámico aproximado.
- Persistencia temporal de clipping.

Objetivo:

- Penalizar imagen inutilizable por clipping prolongado.
- No penalizar automáticamente reflejos especulares, sol o una zona pequeña brillante.

Perfiles log/HDR:

- Detectar tags de color cuando estén disponibles.
- En MVP, marcar un aviso de calibración/fiabilidad reducida para material log/HDR antes que tratarlo con una curva SDR incorrecta.

### 3.3 Movimiento y suavidad

Usar optical flow o transformaciones globales estimadas sobre imágenes reducidas y con máscaras/robustez para evitar que un sujeto móvil domine el cálculo.

Derivar:

- Magnitud media de movimiento global.
- Dirección dominante.
- Cambio de velocidad entre muestras.
- Cambio de aceleración o jerk aproximado.
- Proporción de inliers en estimación RANSAC.

Interpretación inicial:

- Movimiento bajo y estable: potencialmente bueno para tomas estáticas/hover.
- Movimiento moderado con dirección y velocidad coherentes: deseable para cine.
- Picos repetidos de aceleración/rotación: penalización de maniobra brusca.
- Movimiento alto pero consistente: posible FPV bueno; clasificar según perfil, no descartar por defecto.

### 3.4 Estabilidad

Estimar transformaciones afines/parciales entre frames y analizar:

- Traslación, rotación y escala.
- Variación de esos parámetros entre frames.
- Número de fallos de tracking.

No usar «poco movimiento» como sinónimo de «estable». La estabilidad equivale a previsibilidad/coherencia, no a inmovilidad.

### 3.5 Frames problemáticos

Detectar y penalizar:

- Frames casi negros o casi blancos sostenidos.
- Frames congelados/duplicados anómalos.
- Errores de decodificación reportados por FFmpeg.
- Inicio y final de clip con cambios extremos, tratándolos como posibles despegues, aterrizajes o manipulación de cámara.

## 4. Normalización y score

Mantener scores separados y un score compuesto configurable:

\[
S_t = w_s S_{sharp} + w_e S_{exposure} + w_m S_{motion} + w_{st} S_{stability} + w_f S_{frame\_health}
\]

Condiciones:

- Los pesos suman 1.
- Los perfiles definen pesos y umbrales, no código duplicado.
- El score compuesto nunca debe ocultar los scores individuales.
- Las penalizaciones graves deben poder limitar el score final aunque otras señales sean altas.

Configuración orientativa para perfil `cinematic_drone_v1`:

```yaml
weights:
  sharpness: 0.28
  exposure: 0.20
  motion_smoothness: 0.28
  stability: 0.18
  frame_health: 0.06
thresholds:
  enter_segment_score: 0.72
  exit_segment_score: 0.62
  minimum_duration_seconds: 4.0
  merge_gap_seconds: 1.0
  handle_seconds: 0.5
```

Estos valores son hipótesis iniciales; deben quedar documentados, configurables y calibrados con datos etiquetados.

## 5. Perfiles iniciales

| Perfil | Intención | Comportamiento |
|---|---|---|
| `cinematic_drone_v1` | Vuelos lentos, reveals, órbitas y travellings | Penaliza jerk y vibración con fuerza; premia movimiento homogéneo |
| `fpv_controlled_v1` | FPV con dinámica deliberada | Tolera velocidad y rotación mayores; penaliza irregularidad y golpes, no intensidad |
| `static_aerial_v1` | Hover, paisajes y planos fijos | Premia baja variación; exige nitidez y exposición consistentes |

## 6. Construcción de segmentos

Pseudológica:

1. Suavizar scores de ventana con filtro temporal robusto.
2. Abrir un candidato cuando `score >= enter_threshold`.
3. Mantenerlo mientras `score >= exit_threshold`.
4. Cerrar al caer por debajo del umbral de salida durante una duración de gracia.
5. Descartar candidatos menores que `minimum_duration_seconds`.
6. Unir candidatos separados por un hueco menor que `merge_gap_seconds` si el hueco no contiene penalización crítica.
7. Aplicar handles sin superar límites de clip y sin introducir tramos de muy baja calidad.
8. Adjuntar razones basadas en métricas dominantes y penalizaciones.

## 7. Salidas y depuración

Por clip, persistir:

- Serie de ventanas con timestamps y métricas crudas/normalizadas.
- Segmentos candidatos y versión del algoritmo.
- Artefactos opcionales: gráfica de scores y frames representativos.
- Resumen de diagnóstico: FPS de muestreo, duración analizada, frames procesados, fallos de decodificación y tiempo de ejecución.

## 8. Futuras señales

No implementar hasta validar MVP:

- Horizonte y roll involuntario.
- Clasificación de despegue/aterrizaje.
- Detección de hélices, patas, obstáculos o persona operando.
- Duplicados mediante embeddings visuales.
- Calidad estética con modelos BVQA/VLM.
- Uso de telemetría SRT/DJI si existe y es legal/técnicamente accesible.
- Modelo personalizado entrenado con aprobaciones/rechazos del usuario.

---

## `docs/DATA_MODEL.md`

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

---

## `docs/UX_SPEC.md`

# Especificación UX — EditorAgent

## 1. Principio UX

La interfaz debe parecer una mesa de selección, no un panel de IA opaco. La prioridad es revisar muchas decisiones con velocidad, comprender el motivo de cada sugerencia y conservar el control editorial.

## 2. Flujo principal

1. Crear/abrir proyecto.
2. Añadir carpeta(s) de medios.
3. Revisar inventario y avisos de compatibilidad.
4. Elegir perfil de análisis y parámetros básicos.
5. Lanzar análisis y observar progreso sin bloquear la aplicación.
6. Revisar segmentos ordenados por score o agrupados por clip.
7. Aprobar/rechazar/ajustar intervalos con teclado y visualización.
8. Filtrar por estado, score, duración, clip o etiquetas.
9. Exportar selects y abrirlos en el NLE de destino.

## 3. Pantallas MVP

### Inicio/proyectos

- Lista de proyectos recientes.
- Crear proyecto con nombre y carpeta de artefactos.
- Acceso a diagnóstico y preferencias.

### Ingestión

- Selector de carpetas.
- Tabla de clips: nombre, duración, codec, resolución, estado y warning.
- Confirmación visible: «Los originales se analizan en modo sólo lectura».
- Botón de iniciar análisis sólo cuando hay clips válidos.

### Configuración de análisis

- Perfil: Cinemático, FPV controlado, Aéreo estático.
- Duración mínima.
- Nivel de selección: conservador/equilibrado/generoso, que mapea a presets transparentes.
- Opción de generar proxies/thumbnails.
- En modo avanzado: pesos y umbrales, con restauración de valores del perfil.

### Revisión

Layout recomendado:

```text
┌─────────────────────────────────────────────────────────────┐
│ Proyecto · análisis · filtros · exportar                     │
├──────────────┬───────────────────────────────┬──────────────┤
│ Clips/       │ Player proxy + timeline       │ Inspector    │
│ segmentos    │ filmstrip + curvas de score   │ score,       │
│ ordenables   │ in/out ajustables             │ razones,     │
│              │                               │ acciones     │
└──────────────┴───────────────────────────────┴──────────────┘
```

Acciones rápidas:

- `A`: aprobar.
- `R` o `X`: rechazar.
- `M`: marcar como manual tras editar el rango.
- Flechas/J/K/L: navegación/reproducción si se implementa una convención coherente.
- `1–5`: etiquetado/rating opcional posterior.

No fijar atajos definitivos sin comprobación de conflictos y accesibilidad.

### Exportación

- Elegir formato.
- Elegir subconjunto: aprobados, sugeridos por encima de score, todos con filtros actuales.
- Elegir destino fuera de las carpetas fuente por defecto.
- Mostrar resumen: número de segmentos, duración total y advertencias de compatibilidad.
- Mostrar resultado y abrir carpeta sólo por acción del usuario.

## 4. Explicabilidad visible

Cada segmento debe mostrar frases legibles, por ejemplo:

- «Movimiento constante durante 8,4 s».
- «Nitidez alta en 93% de las muestras».
- «Exposición equilibrada; clipping de altas luces bajo».
- «Penalización: aceleración brusca entre 00:12,5 y 00:13,1».
- «Confianza limitada: material HDR/log detectado».

Evitar mensajes como «IA score: 0.84» sin contexto.

## 5. Manejo de incertidumbre

- Usar «sugerido», no «bueno» o «malo» como etiqueta absoluta.
- Separar filtros técnicos de criterios estéticos cuando se añadan.
- Permitir al usuario ocultar una métrica irrelevante para su tipo de vuelo.
- Mostrar warnings cuando el análisis use proxy, muestreo reducido o métricas con baja fiabilidad.

## 6. Accesibilidad y robustez

- Estados no diferenciados sólo por color.
- Controles operables por teclado.
- Texto y tooltips en español inicialmente; preparar internacionalización.
- Confirmación antes de borrar artefactos de proyecto, nunca los originales.
- Progreso detallado y cancelación siempre visible durante tareas largas.

---

## `docs/EVALUATION.md`

# Plan de evaluación y dataset — EditorAgent

## 1. Objetivo

Medir si EditorAgent ahorra tiempo y propone segmentos útiles, no sólo si calcula métricas visualmente elegantes.

## 2. Dataset inicial

Crear un dataset privado, con consentimiento y sin publicar brutos de clientes, de al menos:

- 30 a 50 clips representativos para iterar heurísticas.
- Mezcla de cine drone, órbitas, reveals, seguimiento, hover y FPV controlado.
- Casos difíciles: viento/vibración, baja luz, agua/reflejos, contraluz, niebla, textura baja, movimientos deliberadamente rápidos y clips con errores.
- Diferentes resoluciones, FPS, codecs y, si aplica, perfiles log/HDR.

Para cada clip, guardar:

- Metadata técnica.
- Anotaciones humanas de intervalos `usable`, `unusable` y `uncertain`.
- Motivo predominante del descarte: blur, exposición, jerk, despegue/aterrizaje, redundancia, contenido no deseado, etc.
- Perfil de intención: cinematic, fpv, static u otro.

## 3. Protocolo de etiquetado

- Un intervalo útil debe tener duración mínima definida por el caso de uso.
- Anotar bordes con tolerancia; no asumir que dos editores escogerán el mismo frame exacto.
- Separar «técnicamente malo» de «técnicamente válido pero narrativamente innecesario».
- Si es posible, obtener dos anotadores para una parte del dataset y registrar desacuerdos.

## 4. Métricas

### Selección temporal

- Precision: proporción de tiempo sugerido que coincide con material etiquetado útil.
- Recall: proporción de material útil que EditorAgent encuentra.
- Intersection over Union temporal por segmento cuando corresponda.
- Cobertura de tomas útiles entre los N mejores resultados.

### Utilidad humana

- Tasa de aprobación de sugerencias.
- Tiempo hasta primera selección aprobada.
- Minutos de material revisado para producir un minuto de selects.
- Número de ajustes de in/out por sugerencia.
- Valoración cualitativa: «¿me ahorró tiempo?».

### Rendimiento

- Tiempo de análisis por minuto de vídeo en CPU y GPU opcional.
- RAM máxima.
- Tamaño de proxies y artefactos.
- Tasa de fallos por codec/tipo de archivo.

## 5. Baselines obligatorios

Comparar el algoritmo nuevo contra:

1. Sin selección automática: visionado manual.
2. Score simple de nitidez + exposición.
3. Score completo del perfil actual.

No afirmar mejoras si no supera los baselines con el mismo dataset y protocolo.

## 6. Pruebas sintéticas

Mantener clips o imágenes de prueba creados con licencia apropiada para validar invariantes:

- Blur creciente.
- Variaciones de exposición y clipping.
- Movimiento lineal suave.
- Jerk o cambios abruptos sintéticos.
- Frame congelado.
- Vídeo VFR o timestamps irregulares si se dispone de fixture.

Estas pruebas no sustituyen material real, pero evitan regresiones.

## 7. Criterio de paso MVP

No fijar porcentajes de precisión universales antes de tener datos, pero exigir evidencia de que para el perfil primario:

- El top de sugerencias contiene una proporción claramente útil de material.
- El usuario puede descartar/revisar rápidamente falsos positivos.
- El tiempo total de llegar a una selección disminuye frente al visionado lineal.
- No hay pérdida ni modificación de fuentes.

---

## `docs/SECURITY_PRIVACY.md`

# Seguridad y privacidad — EditorAgent

## 1. Postura de privacidad

EditorAgent se diseña como software local-first. El análisis, proxies, métricas, decisiones y exportaciones se realizan localmente por defecto. No se requieren cuentas ni se suben vídeos.

## 2. Reglas de protección de medios

- Abrir medios fuente en modo lectura.
- Nunca escribir en la carpeta de los originales por defecto.
- Separar explícitamente medios fuente y carpeta de proyecto.
- Antes de cualquier operación potencialmente destructiva sobre artefactos, mostrar qué se borrará y conservar los originales fuera de alcance.
- Registrar la ruta fuente y huella del archivo sin incluir contenido sensible en logs de diagnóstico cuando no sea necesario.

## 3. Redes y modelos

- La aplicación no realiza llamadas de red sin una función explícita y consentimiento del usuario.
- Si se ofrecen actualizaciones de modelos o servicios cloud futuros, deben estar separados del análisis local, mostrar tamaño/licencia/destino y requerir opt-in.
- Documentar si cualquier modelo recoge telemetría o realiza consultas externas; preferir modelos que no lo hagan.

## 4. Datos de diagnóstico

- Los logs permanecen locales.
- Una función de «exportar diagnóstico» debe previsualizar el contenido y advertir qué datos incluye antes de compartirlo.
- Evitar guardar rutas completas, nombres de clientes o GPS en reportes compartibles por defecto; ofrecer redacción.

## 5. Dependencias y supply chain

- Fijar versiones y generar lockfiles.
- Revisar licencias de FFmpeg, OpenCV, modelos y dependencias de UI antes de distribución comercial.
- Automatizar análisis de dependencias y vulnerabilidades en CI cuando sea posible.
- No ejecutar binarios descargados sin verificación de procedencia e integridad.

## 6. Permisos y empaquetado

- Pedir acceso únicamente a carpetas seleccionadas por el usuario.
- Declarar de forma clara permisos de filesystem, GPU, aceleración de vídeo y red si existieran.
- Evitar ejecutar como administrador.

## 7. Consideraciones de material aéreo

El metraje de dron puede contener ubicaciones, caras, matrículas y activos de clientes. La privacidad local-first no sustituye las obligaciones legales de cada usuario respecto al uso, almacenamiento y distribución de ese material.

---

## `docs/ROADMAP.md`

# Roadmap — EditorAgent

## Fase 0 — Descubrimiento y definición

**Objetivo:** validar el problema y convertir «tomas fluidas» en criterios observables por perfil.

Entregables:

- Dataset privado inicial etiquetado.
- Confirmación del perfil de usuario prioritario.
- Muestra real de códecs, resoluciones, drones y NLEs.
- Definición de tiempo de análisis aceptable.
- Decisiones registradas en `DECISIONS.md`.

Criterio de salida:

- Al menos 30 clips anotados.
- Un flujo manual de referencia descrito y cronometrado.
- Una hipótesis de producto concreta que se pueda probar.

## Fase 1 — Núcleo técnico CLI

**Objetivo:** demostrar que el pipeline funciona sin UI.

Entregables:

- CLI para crear proyecto e inventariar clips.
- Integración robusta ffprobe.
- Generación opcional de proxies/thumbnails.
- Análisis inicial de nitidez, exposición y movimiento.
- JSON/CSV por clip con series de scores y segmentos candidatos.
- Tests con fixtures y errores por clip.

Criterio de salida:

- Un directorio real se procesa sin modificar originales.
- El CSV contiene intervalos válidos, trazables y explicables.
- Se pueden inspeccionar errores y reanudar trabajos.

## Fase 2 — Heurística de segmentos y evaluación

**Objetivo:** mejorar utilidad con datos, no intuición.

Entregables:

- Perfiles `cinematic_drone_v1`, `fpv_controlled_v1`, `static_aerial_v1`.
- Hysteresis, duración mínima, merge gaps y handles.
- Dataset anotado y script de evaluación.
- Comparativa con baseline de nitidez+exposición.
- Informe de falsos positivos/falsos negativos.

Criterio de salida:

- Mejora demostrable frente al baseline en material primario.
- Falsos positivos interpretables y parámetros ajustables.

## Fase 3 — API local y UI de revisión

**Objetivo:** convertir resultados en flujo de trabajo útil.

Entregables:

- FastAPI local y cola de jobs.
- UI React con proyectos, ingestión, progreso y revisión.
- Reproductor proxy, filmstrip, inspector y atajos de aprobar/rechazar.
- Persistencia de decisiones.
- CSV estable y primera exportación FCPXML validada.

Criterio de salida:

- Un usuario externo puede completar un proyecto sin usar terminal.
- Puede revisar decenas de segmentos con fluidez y exportar una selección.

## Fase 4 — Producto desktop y robustez

**Objetivo:** preparar pruebas reales de mercado.

Entregables:

- Empaquetado Tauri/instalador para Windows.
- Gestión de dependencias/bundle FFmpeg con revisión de licencia.
- Diagnóstico local, recuperación y migraciones.
- Manejo de VFR, orientación y avisos color/HDR.
- Pruebas de rendimiento en hardware objetivo.

Criterio de salida:

- Instalación reproducible en una máquina limpia.
- Procesamiento estable de proyectos de prueba realistas.

## Fase 5 — Inteligencia avanzada

**Objetivo:** aumentar calidad sin sacrificar control ni privacidad.

Posibles entregables, priorizados por evidencia:

- Detección de redundancia con embeddings.
- Detección de despegue/aterrizaje.
- Horizonte/roll y clasificación de tipo de movimiento.
- Score estético opcional y claramente separado.
- Aprendizaje de preferencias basado en feedback local.
- Aceleración GPU opcional.

Criterio de salida:

- Cada capacidad mejora una métrica de evaluación o una métrica de tiempo de usuario.
- Las funciones se pueden desactivar y sus límites se explican.

## Fase 6 — Validación comercial

**Objetivo:** decidir si existe un producto sostenible.

Experimentos:

- Beta cerrada con pilotos/editores reales.
- Medición de sesiones, tiempo ahorrado y retención con opt-in respetuoso.
- Entrevistas sobre precio, compatibilidad y confianza.
- Comparar licencia perpétua, pago por versión y suscripción opcional sin bloquear análisis local.

No construir un plan de monetización definitivo antes de observar uso repetido y valor claro.

---

## `docs/DECISIONS.md`

# Registro de decisiones — EditorAgent

Usa este documento como ADR ligero. No borres decisiones antiguas: márcalas como reemplazadas y enlaza la nueva.

## Plantilla

```markdown
## ADR-XXX — Título corto

- Fecha: YYYY-MM-DD
- Estado: propuesta | aceptada | reemplazada | rechazada
- Contexto:
- Decisión:
- Alternativas consideradas:
- Consecuencias:
- Evidencia/enlaces internos:
```

## ADR-001 — Local-first y originales inmutables

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: El material de dron puede ser privado, pesado y crítico. Subirlo o modificarlo reduce confianza y aumenta coste.
- Decisión: La primera versión procesa localmente y no escribe en las carpetas fuente. Todos los proxies, resultados y exports se guardan en una carpeta de proyecto separada.
- Alternativas consideradas: procesamiento cloud por defecto; crear subclips junto a originales.
- Consecuencias: Mayor complejidad de empaquetado y rendimiento local; ventaja de privacidad, control y aceptación profesional.

## ADR-002 — Heurísticas antes que modelos complejos

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: Un modelo estético general puede ser opaco, pesado y poco alineado con la intención de vuelo.
- Decisión: El MVP usa señales interpretables de nitidez, exposición, movimiento, estabilidad y salud de frame. Los modelos ML se incorporan sólo tras evaluación comparativa y revisión de licencias.
- Alternativas consideradas: empezar con un VLM/BVQA como score central.
- Consecuencias: Menor «wow» inicial, mayor capacidad de depuración, calibración y confianza.

## ADR-003 — CSV como exportación de referencia

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: Las integraciones NLE y XML tienen variaciones.
- Decisión: CSV legible y completo es la salida base. FCPXML y EDL se implementan de forma incremental con fixtures y validación real.
- Alternativas consideradas: depender exclusivamente de XML específico de un editor.
- Consecuencias: El usuario siempre tiene una salida reutilizable, aunque una integración concreta falle.

---

## `docs/DEVELOPMENT_PROMPT.md`

# Prompt maestro de desarrollo — EditorAgent

Copia este prompt al iniciar una sesión con un agente de código que tenga acceso al repositorio.

```text
Estás desarrollando EditorAgent. Lee primero y completa las instrucciones de AGENTS.md. Después lee README.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/ANALYSIS_SPEC.md, docs/DATA_MODEL.md, docs/UX_SPEC.md, docs/EVALUATION.md, docs/ROADMAP.md, docs/SECURITY_PRIVACY.md y docs/DECISIONS.md.

Contexto de producto:
EditorAgent es una aplicación local-first para analizar clips, inicialmente de dron, y proponer segmentos técnicamente utilizables: nítidos, correctamente expuestos, sin fallos y con movimiento estable/coherente. No modifica originales y no sustituye el criterio editorial humano. Debe guardar resultados explicables, permitir revisión rápida y exportar selecciones hacia un NLE.

Tu forma de trabajar:
1. Resume en un máximo de 10 líneas lo que entiendes que hay que entregar en esta tarea y enumera los archivos que cambiarás.
2. Identifica ambigüedades que afecten la arquitectura o la definición de éxito. Si son bloqueantes, formula hasta 5 preguntas concretas con una recomendación por pregunta y espera respuesta. Si no son bloqueantes, declara el supuesto mínimo que usarás.
3. Propón un plan de implementación por pasos verificables, incluyendo pruebas y criterios de aceptación.
4. Implementa sólo el siguiente entregable vertical más pequeño que aporte valor real. No intentes construir todo el producto de una vez.
5. Conserva los originales en modo sólo lectura. No uses operaciones destructivas ni escribas artefactos dentro de carpetas fuente.
6. Separa dominio, infraestructura, workers, analizadores, exporters y UI. No metas lógica de visión o FFmpeg en componentes React.
7. Para vídeo, invoca FFmpeg/ffprobe con listas de argumentos seguras, sin shell string interpolation. Trata rutas con espacios, VFR, rotación y errores de codec como escenarios normales.
8. Implementa análisis por streaming/muestreo; nunca cargues un clip entero en RAM. Los jobs deben ser cancelables, reanudables y tolerantes a fallo por clip.
9. Cada score debe conservar sus componentes, parámetros y explicaciones legibles. No presentes un score como verdad creativa.
10. Añade tests a toda lógica determinista. Ejecuta format, lint, type-check y tests relevantes antes de terminar.
11. Actualiza la documentación afectada y registra decisiones relevantes en docs/DECISIONS.md.
12. Al finalizar, responde con: resumen de cambios, decisiones/supuestos, comandos ejecutados y resultados, archivos clave, limitaciones conocidas y próximo paso recomendado.

Prioridades:
1) Integridad de fuentes y privacidad local.
2) Corrección y trazabilidad.
3) Flujo útil para revisión humana.
4) Rendimiento para clips 4K/HEVC.
5) Mantenibilidad.
6) IA avanzada opcional.

Restricciones:
- Runtime de análisis: Python 3.12+, FFmpeg/ffprobe, OpenCV.
- API local: FastAPI; DB: SQLite; UI: React + TypeScript + Vite; desktop futuro: Tauri.
- Debe funcionar con CPU; GPU sólo como mejora opcional.
- CSV es el primer contrato de exportación; FCPXML/EDL deben validarse antes de prometer compatibilidad.
- No hay cloud, cuentas ni telemetría por defecto.

Tarea actual:
[PEGA AQUÍ UNA TAREA CONCRETA, POR EJEMPLO: "Implementa Fase 1 / vertical slice 1: CLI que crea un proyecto, inventaría MP4/MOV de una carpeta usando ffprobe y escribe un manifest JSON/CSV sin generar proxies todavía."]
```

## Cómo formular tareas buenas al agente

Una tarea por sesión o PR. Ejemplos, en orden:

1. «Inicializa el monorepo y la configuración de calidad Python/TypeScript conforme a los documentos. No implementes aún análisis de vídeo.»
2. «Implementa el modelo SQLite y CLI `project create` / `media scan`, con tests para rutas y archivos no soportados.»
3. «Implementa un adaptador ffprobe seguro que extraiga y normalice metadatos a `Clip`, usando fixtures JSON reales/anónimos.»
4. «Implementa la generación de proxy y thumbnails como job cancelable, sin alterar las fuentes.»
5. «Implementa análisis de nitidez y exposición por ventanas, persistencia de resultados y CSV de diagnóstico.»
6. «Implementa estimación de movimiento global y score de suavidad para el perfil cinematic.»
7. «Implementa SegmentBuilder con hysteresis, duración mínima, unión de gaps y tests de series sintéticas.»
8. «Construye el script de evaluación sobre clips anotados y compáralo con baseline.»
9. «Expón proyectos, clips, runs y segmentos mediante API FastAPI con contratos tipados.»
10. «Implementa la UI de ingestión, lanzamiento de análisis y progreso.»
11. «Implementa la pantalla de revisión con player proxy, segmentos, inspector y aprobar/rechazar.»
12. «Implementa exportación CSV completa y valida FCPXML con un proyecto de prueba.»

---

## `docs/QUESTIONS_FOR_FOUNDER.md`

# Preguntas para el fundador — EditorAgent

Estas decisiones no impiden crear el esqueleto, pero deben responderse antes de optimizar el producto o elegir una arquitectura definitiva. Responde en este archivo con `Respuesta`, `Decisión` y, si existe, `Evidencia`.

## 1. Usuario y mercado

1. ¿Quién es el primer usuario pagador o beta tester: piloto de dron individual, editor freelance, productora, inmobiliaria, operador FPV, estudio audiovisual u otro?
2. ¿Qué dolor concreto debe resolver primero: ahorrar visionado, entregar selects a un editor, montar highlights, organizar un archivo de clips o detectar fallos técnicos?
3. ¿Qué frecuencia de uso esperas: cada vuelo, semanal, por proyecto grande, por lote de tarjetas?
4. ¿Qué alternativas usa hoy ese usuario y cuánto tiempo tarda en hacer la selección manual?
5. ¿Cuál sería una señal inequívoca de que el producto aporta valor: minutos ahorrados, tasa de aprobación, menos estrés, más clips aprovechados, entrega más rápida?

## 2. Tipos de vuelo y criterio creativo

6. Ordena por prioridad: dron cinemático lento, inmobiliario, paisaje/turismo, eventos, FPV, seguimiento de vehículos/deporte, inspección u otros.
7. Describe tres tomas que EditorAgent debería marcar como muy buenas aunque sean visualmente distintas.
8. Describe tres tomas que debería descartar casi siempre.
9. Para FPV: ¿qué movimientos intensos son intencionales y no deberían penalizarse?
10. ¿La herramienta debe evaluar únicamente calidad técnica en MVP o también interés visual/composición?
11. ¿Qué duración mínima típica te resulta útil: 2, 3, 5, 8, 10 segundos? ¿Depende del tipo de proyecto?

## 3. Material real

12. ¿Qué drones/cámaras usarás primero? Indica modelos si quieres.
13. ¿Qué formatos son habituales: MP4/MOV, H.264/H.265, 4K/5.1K, 24/25/30/50/60 fps, 8/10-bit?
14. ¿Grabación normal, D-Log, HLG, HDR o mezcla?
15. ¿Sueles tener telemetría, subtítulos SRT o metadata DJI disponible junto al vídeo?
16. ¿Trabajas con clips largos o muchos clips cortos? Da una sesión típica: número de clips, duración total y tamaño.
17. ¿Qué hardware usarán los primeros usuarios: Windows/macOS, CPU, GPU, RAM, almacenamiento?
18. ¿Puedes aportar 30–50 clips no sensibles para crear el dataset de evaluación y etiquetarlos?

## 4. Flujo de edición

19. ¿Qué NLE debe ser prioritario: DaVinci Resolve, Premiere Pro, Final Cut, CapCut u otro?
20. ¿Qué salida sería más valiosa primero: CSV, XML/FCPXML, EDL, markers, subclips físicos, proxies seleccionados o una timeline ya montada?
21. ¿Quieres que EditorAgent sea una app independiente, un companion que lanza Resolve/Premiere, un plugin futuro o una CLI/API para integrarlo en tus automatizaciones?
22. ¿Necesitas conservar timecode de cámara para relink profesional?
23. ¿Los nombres y estructura de carpetas de cliente deben preservarse exactamente?

## 5. Producto y negocio

24. ¿El objetivo inicial es una herramienta interna para Flopwork/proyectos propios, un producto comercial o ambos?
25. ¿Prefieres licencia de escritorio, pago único, suscripción, uso por créditos cloud opcional, open core u otra estrategia?
26. ¿Qué nivel de configuración tolerará el usuario objetivo: presets simples, controles avanzados o ambos?
27. ¿Cuál es el precio aproximado que imaginarías si el producto ahorrara tiempo de forma demostrable?
28. ¿Qué debe diferenciarlo claramente frente a una función genérica de IA de un editor?

## 6. Privacidad, rendimiento e IA

29. ¿Debe ser 100% offline siempre, o aceptas descargas opcionales de modelos y/o procesamiento cloud voluntario?
30. ¿Tiempo de análisis tolerable por 60 minutos de material: 5 min, 15 min, 30 min, 1 h? Diferencia CPU/GPU si procede.
31. ¿Qué pesa más: precisión de selección, velocidad o bajo consumo de recursos?
32. ¿Aceptarías que el sistema aprenda de tus aprobaciones/rechazos localmente? ¿Quieres poder desactivar/borrar ese aprendizaje?
33. ¿Hay requisitos de privacidad o clientes para los que el cloud sea inaceptable?

## 7. Validación

34. ¿Con qué 3–5 personas podrías probar una beta?
35. ¿Qué proyecto real próximo podríamos usar como prueba de extremo a extremo?
36. ¿Cómo compararás objetivamente EditorAgent con tu proceso actual?
37. ¿Qué fracaso temprano te haría abandonar o redirigir la idea?

## Prioridad de respuesta

Para empezar Fase 1 responde, como mínimo, las preguntas 1, 2, 6, 10, 12–17, 19–21, 24, 29–31 y 35.
