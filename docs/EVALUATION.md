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

## 8. Herramienta inicial de evaluación

Las anotaciones privadas se guardan como JSON dentro de una carpeta de evaluación separada
del material original. Cada intervalo debe tener `start_seconds`, `end_seconds` y una etiqueta
como `usable`, `technical_bad`, `intentional_dynamic`, `abrupt_motion`, `uncertain` o
`takeoff_landing`.

Crear una plantilla a partir de las ventanas producidas por un análisis:

```powershell
editoragent evaluation template `
	analysis/<run-id>_windows.json `
	evaluation/annotations/clip.json `
	--clip-id <clip-id> `
	--relative-path DJI_clip.mp4
```

Después de etiquetar los intervalos, comparar el score completo con el baseline de nitidez y
exposición:

```powershell
editoragent evaluation windows `
	analysis/<run-id>_windows.json `
	evaluation/annotations/clip.json `
	--enter-threshold 0.72 `
	--top-k 5
```

El resultado incluye precision, recall, `precision_at_k`, ventanas predichas y cantidad de
ventanas aún sin etiquetar. Esta primera versión evalúa ventanas, no sustituye todavía la
revisión temporal de segmentos con tolerancia IoU; esa será la siguiente ampliación.

## 9. Evaluación como flujo de producto

La herramienta principal será también el instrumento de etiquetado. Cada sesión de selección puede
producir dos salidas independientes:

- Selects editoriales para DaVinci Resolve.
- Dataset privado con intervalos, etiquetas, métricas, perfil y decisión humana.

La UI debe permitir etiquetar mientras se revisa, sin obligar a repetir el clip en una pantalla de
calibración separada. Las etiquetas estructuradas se almacenarán en SQLite y podrán exportarse a
JSON/CSV para crear versiones `development`, `validation` y `test` separadas por vuelo o sesión.

El monitor de aprendizaje contará decisiones y cobertura, pero no presentará esas cifras como
entrenamiento de un modelo hasta que exista una ejecución reproducible y validada.
