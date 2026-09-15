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

## Plan de precisión — prioridad transversal actual

El valor del producto depende primero de recuperar tomas buenas y explicar por qué se
han seleccionado. Esta línea de trabajo precede a la integración de modelos pesados.

### Estado actual — 2026-09-15

- Pipeline heurístico de nitidez, exposición, movimiento, estabilidad y segmentos: implementado.
- API/UI de inventario, análisis individual, análisis por lote, progreso, cancelación y revisión: implementada.
- Perfiles versionados y catálogo API: implementados; falta el backoffice visual de tweaking.
- Plantillas, calibración UI, IoU temporal y métricas iniciales: implementadas; falta acumular etiquetas reales.
- `HumanLabel`, `LabelingSession`, etiquetado desde el inspector y segmentos manuales: implementados.
- Workspace unificado de selección y adquisición de conocimiento: implementado; falta validarlo con una sesión real de etiquetado.
- Exportación editorial FCPXML/EDL y dataset de conocimiento JSON/CSV: implementada.
- Navegación rápida, atajos, monitor de cobertura y datasets versionados: implementados.
- Clasificación de tipos de movimiento: pendiente.
- Embeddings, BVQA y VLM: investigación completada; integración pendiente y condicionada a métricas.

### Orden de entregas

1. **Perfiles de análisis:** extraer pesos y umbrales a una configuración versionada; incluir
	`cinematic_traveling`, `fpv_controlled`, `static_aerial` y `recall_high`.
2. **Evaluación etiquetada:** etiquetar ventanas reales por utilidad, tipo de movimiento y
	motivo de descarte; crear baseline y métricas de precision, recall, temporal IoU y Precision@K.
3. **Trayectoria de cámara:** añadir rotación, escala, inliers, aceleración, jerk y confianza;
	separar intensidad de movimiento de irregularidad.
4. **Backoffice:** permitir seleccionar perfil, ajustar parámetros, guardar presets y comparar
	resultados sin perder versiones anteriores.
5. **Personalización local:** usar aprobaciones, rechazos y ajustes del usuario para entrenar
	un modelo tabular ligero por perfil, con validación por vuelo.
6. **Redundancia:** probar DINOv2 sobre frames representativos para agrupar tomas equivalentes
	y conservar diversidad, sin mezclarlo con el score técnico.
7. **IA opcional:** evaluar BVQA/VLM bajo demanda y sólo conservarlos si mejoran métricas o
	reducen tiempo de revisión; siempre deben poder desactivarse y ejecutarse localmente.

### Criterio de avance

No se considera mejor una versión porque produzca más candidatos. Cada entrega debe comparar
contra el baseline congelado y mostrar qué falsos negativos recupera, qué falsos positivos añade,
el coste de análisis y el resultado por perfil. El objetivo inicial es maximizar el recall de
tomas utilizables sin hacer inviable la revisión.

### Reorientación de producto — workspace de adquisición de conocimiento

La evaluación etiquetada no será una utilidad secundaria basada en terminal. El workspace principal
de selección será el lugar donde el usuario analiza, corta, revisa, etiqueta y exporta. Cada decisión
humana conservará su procedencia y podrá alimentar versiones privadas del dataset.

Orden de implementación de este cambio mayor:

1. Modelo persistente de etiquetas humanas y sesiones de etiquetado, sin romper `Segment`.
2. Workspace unificado con reproductor, timeline, segmentos del clip, atajos y navegación siguiente.
3. Exportación dual: FCPXML editorial y JSON/CSV de conocimiento.
4. Monitor de cobertura y discrepancias entre sistema y usuario.
5. Dataset versionado y evaluación temporal por IoU.
6. Modelo local ligero sobre feedback, sólo después de disponer de ejemplos suficientes.
7. Backoffice técnico de tweaking separado de la interfaz normal.

### Siguiente bloque activo

Antes de mejorar la trayectoria o introducir IA, se cerrará el circuito de trabajo humano:

1. Navegación rápida entre clips y segmentos.
2. Edición IN/OUT y creación manual con atajos.
3. Exportación editorial FCPXML y exportación de conocimiento JSON/CSV separadas.
4. Monitor de cobertura de etiquetas y discrepancias sistema/usuario.
5. Evaluación temporal con IoU y dataset versionado.

Sólo después se utilizarán esas decisiones para mejorar movimiento, perfiles y modelos locales.

El bloque técnico anterior está cerrado. La siguiente actividad requiere trabajo humano sobre
clips reales: etiquetar una primera sesión representativa, revisar el monitor y exportar una
versión del dataset antes de cambiar el detector.
