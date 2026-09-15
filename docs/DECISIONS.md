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

## ADR-004 — Alcance y prioridades de arranque de Fase 1

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: Sesión de pressure-testing (grill-me) para cerrar ambigüedades antes de implementar el CLI de Fase 1. Ver `docs/QUESTIONS_FOR_FOUNDER.md` § "Respuestas cerradas".
- Decisión:
  - Uso interno primero, no comercial desde el día 1.
  - Perfil prioritario a calibrar: `cinematic_drone_v1`, aunque el dron de referencia (DJI Avata 2) es técnicamente FPV/cinewhoop; `fpv_controlled_v1` se pospone.
  - Formato de referencia inicial: DJI Avata 2, `.MP4`, H.265/HEVC, 8-bit Normal o 10-bit D-Log M. Fase 1 soporta explícitamente 2-3 formatos propios y falla con error claro en el resto.
  - CPU-only en Fase 1-2; GPU se decide con datos de rendimiento reales, no por adelantado.
  - Offline por defecto; cloud/modelos opcionales quedan fuera de alcance por ahora.
  - NLE de exportación prioritario: DaVinci Resolve (FCPXML) antes que Premiere Pro.
  - Volumen objetivo de Fase 1: lotes de hasta ~50 clips.
  - La duración mínima de segmento (`minimum_duration_seconds`) es un umbral de descarte, no una duración fija de salida; los segmentos conservan su duración natural detectada, con modo "auto" y umbral configurable.
- Alternativas consideradas: empezar directo con perfil FPV (más fiel al dron real); diseñar multi-formato genérico desde ya; comprometerse a GPU desde el inicio.
- Consecuencias: Fase 1 queda acotada y ejecutable con confianza; existe una tensión conocida (Avata 2 es FPV pero se calibra primero como cinemático) que deberá revisarse con datos reales del dataset del usuario antes de generalizar el perfil.

## ADR-005 — Procesar un clip a la vez antes de habilitar batch

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: Para validar que el pipeline (inventario → análisis → segmentos → export FCPXML → import en DaVinci Resolve) es correcto de extremo a extremo, procesar 50 clips a la vez dificulta detectar y depurar fallos: no se sabe qué clip concreto produjo un resultado raro sin revisar todo el lote.
- Decisión: El primer slice de Fase 1 opera sobre **un único clip por invocación** (`media inspect <archivo>`), no sobre una carpeta completa. El comando de escaneo por carpeta/batch (`media scan`) se implementa después, una vez que el flujo de un clip esté verificado manualmente contra DaVinci Resolve.
- Alternativas consideradas: implementar `media scan` de carpeta completa desde el principio (previsto originalmente en ARCHITECTURE.md/ROADMAP.md Fase 1).
- Consecuencias: Se retrasa ligeramente el entregable de "inventario de carpeta", pero se gana confianza real en cada etapa del pipeline antes de escalar a lotes. `media scan` reutilizará la misma lógica de `media inspect` sin duplicar código.

## ADR-006 — Muestreo de frames mediante FFmpeg en streaming

- Fecha: 2026-09-13
- Estado: aceptada
- Contexto: La primera versión del analizador de nitidez/exposición leía el vídeo frame a frame de forma secuencial (`cap.grab()` en cada frame) para preservar timestamps exactos en contenido VFR. Probado contra un clip real (DJI Avata 2, 4K, 100 fps, 232 s, HEVC 10-bit), este enfoque resultó demasiado lento en CPU para ser usable (más de varios minutos sin terminar a 2 fps de muestreo).
- Decisión: `frame_sampler.sample_frames` usa FFmpeg en streaming con el filtro `fps`, `scale` y `format=gray`. FFmpeg decodifica de forma secuencial y entrega sólo las muestras necesarias; Python procesa un frame pequeño cada vez y nunca carga el clip entero. Los timestamps de salida son los timestamps regulares del muestreo.
- Alternativas consideradas: seek aleatorio con OpenCV (falló con errores NAL y podía bloquearse en el HEVC real del Avata 2); leer y decodificar todos los frames en Python (demasiado lento); generar siempre un proxy MP4 antes de analizar (también obliga a recorrer y codificar todo el original, por lo que no acelera el primer análisis).
- Consecuencias: El análisis es robusto con el HEVC real y mantiene bajo el consumo de memoria, pero el primer análisis sigue limitado por la decodificación CPU del original. La generación de proxy se conserva como artefacto opcional para revisión visual futura, no como requisito del análisis técnico. La GPU puede evaluarse después con una medición de rendimiento reproducible.

## ADR-007 — Proxy visual opcional, no prerrequisito del análisis

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: Se implementó caché de proxies en `backend/editoragent/services/proxy_service.py`, pero la prueba real mostró que generar un MP4 640px completo desde un original 4K/100fps obliga igualmente a decodificar todos los frames y puede tardar demasiado en CPU. Convertir el proxy en paso obligatorio no reduce el tiempo del primer análisis.
- Decisión: El análisis técnico usa directamente el sampler FFmpeg en streaming con downscale en memoria. Los proxies se generan sólo cuando un flujo de revisión visual los solicite explícitamente; se guardan dentro de la carpeta del proyecto, nunca junto a los originales, y se invalidan mediante fingerprint.
- Alternativas consideradas: generar siempre el proxy antes de cada análisis; analizar el original a resolución completa; usar seek aleatorio OpenCV.
- Consecuencias: No se duplica trabajo antes del primer resultado. La futura UI podrá reutilizar la caché de proxy para reproducción y thumbnails. El cuello de botella CPU de HEVC sigue existiendo y se medirá antes de decidir aceleración GPU.

## ADR-008 — Medir movimiento antes de juzgarlo

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: El criterio de producto distingue movimiento fluido/intencional de giros bruscos, pero una magnitud alta no significa automáticamente que una toma sea mala, especialmente en FPV.
- Decisión: El primer paso de movimiento calcula únicamente el desplazamiento global entre frames consecutivos mediante correlación de fase. La magnitud normalizada se persiste por ventana como `motion_norm`; no participa todavía en un score compuesto ni aprueba/rechaza segmentos.
- Alternativas consideradas: penalizar directamente cualquier movimiento alto; implementar optical flow, jerk y perfiles de vuelo en el mismo cambio.
- Consecuencias: La señal se puede validar con casos sintéticos y observar en clips reales sin introducir una decisión editorial prematura. El siguiente incremento podrá añadir coherencia de dirección y variación temporal (jerk), usando esta señal ya trazable.

## ADR-009 — Primeros segmentos como candidatos técnicos ajustables

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: Ya existen señales de nitidez, exposición, movimiento, coherencia y jerk, pero todavía no hay calibración suficiente para presentar un score editorial definitivo.
- Decisión: El primer `SegmentBuilder` aplica hysteresis, duración mínima, unión de gaps y handles sobre un `technical_score` provisional. Los umbrales se pueden cambiar desde CLI (`--enter-threshold`, `--exit-threshold`, `--minimum-duration`) y cada ejecución conserva su JSON de ventanas y segmentos.
- Alternativas consideradas: esperar a tener todos los analizadores antes de producir segmentos; marcar los segmentos como automáticamente buenos.
- Consecuencias: El usuario puede empezar a inspeccionar intervalos reales y detectar falsos positivos, pero la salida se denomina siempre “candidato técnico” y no se exporta todavía a un NLE.

## ADR-010 — La confianza de tracking limita, no decide

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: La correlación de fase puede devolver un desplazamiento aunque el frame tenga poca textura o la estimación sea poco fiable. Usar sólo la magnitud produciría movimiento aparente sin evidencia suficiente.
- Decisión: Persistir la respuesta de correlación como `tracking_confidence`, mostrar una penalización legible cuando sea baja y darle un peso limitado en el `technical_score` provisional. No se descarta automáticamente una ventana por esta señal.
- Alternativas consideradas: ignorar la respuesta; descartar cualquier ventana por debajo de un umbral rígido; usarla como sustituto de estabilidad.
- Consecuencias: Los resultados expresan incertidumbre y reducen falsos positivos de movimiento, pero aún necesitamos optical flow/transformaciones robustas y evaluación con metraje real antes de llamar “estable” a una toma.

## ADR-011 — Estabilidad geométrica mediante inliers RANSAC

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: La magnitud y la dirección del desplazamiento no distinguen por sí solas una transformación global coherente de un tracking errático.
- Decisión: Estimar puntos de interés, seguirlos con Lucas-Kanade y ajustar una transformación afín parcial con RANSAC. La proporción de inliers, penalizada por cambios de escala, se persiste como `stability_norm` por ventana.
- Alternativas consideradas: usar sólo la respuesta de correlación de fase; clasificar estabilidad por magnitud baja; introducir un modelo ML antes de tener dataset etiquetado.
- Consecuencias: El pipeline ya puede separar transformaciones sintéticas coherentes de frames sin correspondencia. La métrica sigue siendo técnica y provisional: escenas con pocos detalles, agua, vegetación o sujetos móviles pueden reducir los inliers aunque el plano sea válido.

## ADR-012 — Primer exportador FCPXML como timeline de selects

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: Necesitamos validar visualmente los candidatos sin crear subclips físicos ni modificar los originales. El proyecto ya conserva ruta fuente, FPS, duración e intervalos.
- Decisión: Exportar una secuencia FCPXML 1.10 con un `asset` que referencia el original mediante URI `file:///` y un `asset-clip` por candidato. Los timecodes se redondean al timebase inspeccionado del clip y el XML se escribe únicamente en la carpeta de proyecto.
- Alternativas consideradas: recomprimir subclips; generar primero una timeline propia en la UI; exportar EDL sin validar timecodes.
- Consecuencias: DaVinci Resolve puede revisar los candidatos en una timeline no destructiva. La compatibilidad FCPXML se ha validado estructuralmente y con un archivo real generado; queda pendiente confirmar la importación visual en la instalación de Resolve del usuario.

## ADR-013 — El frameDuration del FCPXML debe ser un frame real

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: La primera importación funcionó, pero Resolve creó una timeline a 24 fps y reprodujo el material acelerado. El XML generado declaraba `frameDuration="1s"` aunque el clip inspeccionado era de 100 fps.
- Decisión: Generar `frameDuration` como la duración de un frame (`fps_den/fps_num`), por ejemplo `1/100s` para 100 fps. Las duraciones y offsets de los clips siguen usando el mismo timebase racional.
- Alternativas consideradas: aceptar el frame rate por defecto de Resolve; forzar siempre 24 fps; crear una timeline manual después de importar.
- Consecuencias: El XML conserva el timebase real del medio y debe evitar la aceleración observada. La importación visual en Resolve debe repetirse con el archivo exportado después de este cambio.

## ADR-014 — Cortar segmentos ante fallos técnicos críticos

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: El primer `SegmentBuilder` podía mantener unido un intervalo largo cuando una ventana intermedia tenía un jerk, tracking o estabilidad claramente malos, porque esas señales sólo reducían el promedio del score.
- Decisión: Añadir umbrales configurables de corte crítico para `jerk_norm`, `stability_norm` y `tracking_confidence`. Una ventana crítica cierra el candidato actual y no se incluye en el tramo siguiente; los tramos buenos anterior y posterior quedan separados.
- Alternativas consideradas: seguir promediando la ventana mala; bajar globalmente el `exit_threshold`; recortar todos los clips a una duración fija.
- Consecuencias: Los candidatos deben representar mejor continuidad técnica y evitar planos artificialmente largos. Los umbrales son hipótesis iniciales y se calibrarán con el dataset real del usuario; no equivalen aún a criterio estético.

## ADR-015 — Detectar giros y frenazos bruscos frame a frame

- Fecha: 2026-09-14
- Estado: aceptada
- Contexto: `jerk_norm` sólo medía diferencias absolutas de magnitud y `direction_coherence` promediaba toda la ventana, por lo que un giro de 180 grados o una parada breve podía quedar diluido.
- Decisión: Calcular el ángulo entre direcciones consecutivas y la caída relativa de magnitud. Los ratios de eventos superados se conservan por ventana, penalizan el score y pueden forzar un corte crítico mediante umbrales configurables.
- Alternativas consideradas: depender sólo de `direction_coherence`; aumentar el peso de `jerk_norm`; analizar el vídeo completo con un modelo ML.
- Consecuencias: Se detectan mejor maniobras bruscas sin confundirlas con cambios suaves. Los umbrales iniciales requieren calibración sobre metraje real y no son un juicio editorial definitivo.

## ADR-016 — El workspace de selección también adquiere conocimiento humano

- Fecha: 2026-09-15
- Estado: aceptada
- Contexto: Una pantalla de calibración separada obliga a repetir trabajo y retrasa la creación del dataset. El producto necesita ser útil para seleccionar tomas antes de disponer de un modelo aprendido.
- Decisión: La interfaz principal será un workspace de selección y etiquetado. El usuario podrá importar, analizar, crear/ajustar segmentos, aprobar/rechazar, etiquetar y exportar desde el mismo flujo. Las decisiones editoriales y las etiquetas de conocimiento se persistirán como conceptos relacionados pero separados.
- Alternativas consideradas: mantener calibración como pantalla aislada; entrenar un modelo grande antes de tener feedback propio; guardar sólo aprobaciones sin etiquetas estructuradas.
- Consecuencias: El producto genera valor inmediato y un dataset privado reutilizable. La UI, el modelo de datos y las exportaciones requieren más cuidado, pero se evita confundir una aprobación editorial con una etiqueta completa de comportamiento.
