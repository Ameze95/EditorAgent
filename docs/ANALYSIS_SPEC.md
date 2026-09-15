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
