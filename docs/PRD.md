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

## 11. Workspace de selección y adquisición de conocimiento

La interfaz principal no separará artificialmente revisión y calibración. Durante las primeras
fases, el usuario utilizará EditorAgent para seleccionar y etiquetar tomas reales; esas decisiones
se conservarán como dataset privado para evaluar y personalizar el analizador.

El workspace debe permitir, sin terminal:

- Cargar y analizar lotes de clips.
- Revisar un clip y pasar al siguiente rápidamente.
- Crear y ajustar segmentos con IN/OUT.
- Aprobar, rechazar y etiquetar cada segmento.
- Exportar selects a DaVinci Resolve mediante FCPXML.
- Exportar las decisiones y métricas como dataset JSON/CSV.
- Consultar el progreso y la cobertura del conocimiento acumulado.

Las decisiones editoriales y las etiquetas de conocimiento son datos relacionados, pero distintos:
aprobar una toma no equivale por sí solo a definir todas sus propiedades de movimiento o tipo de plano.

El backoffice técnico de pesos y umbrales será una sección separada. El usuario normal verá presets
comprensibles; el backoffice conservará el control completo y la trazabilidad de cada ejecución.
- ¿Qué nivel de privacidad se quiere garantizar y comunicar comercialmente?
- ¿Se aceptan modelos descargables opcionales o debe existir un modo portable/offline completo?
