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

## 7. Workspace de selección y etiquetado

La calibración no será un flujo separado del trabajo real. El workspace principal será también la
herramienta para construir el dataset privado del usuario.

```text
┌──────────────────────────────────────────────────────────────┐
│ Sesión · progreso · analizar · exportar                      │
├───────────────┬──────────────────────────────┬───────────────┤
│ Clips          │ Player grande + timeline     │ Inspector     │
│ scroll interno │ IN/OUT + segmentos           │ decisión      │
│ siguiente      │ saltar al segmento           │ etiquetas     │
├───────────────┴──────────────────────────────┴───────────────┤
│ Segmentos y etiquetas del clip seleccionado                  │
└──────────────────────────────────────────────────────────────┘
```

Requisitos de velocidad:

- La lista de clips y la lista de segmentos tendrán scroll interno; se evitará el scroll global largo.
- Hacer clic en un segmento moverá el reproductor a su inicio y lo resaltará.
- Debe existir `Siguiente clip`, `Clip anterior`, `Siguiente segmento` y `Segmento anterior`.
- IN/OUT y etiquetado deben poder realizarse con teclado sin perder el foco del reproductor.
- Las etiquetas se agruparán en decisión, tipo de plano, calidad del movimiento y motivo de rechazo.
- El guardado mostrará estado explícito y nunca perderá etiquetas si se cambia de clip.

## 8. Monitor de aprendizaje

Será una sección separada del workspace de producción. Mostrará conocimiento acumulado, no afirmará
que existe un modelo entrenado hasta que haya una ejecución reproducible.

- Clips y segmentos revisados.
- Aprobaciones, rechazos e incertidumbres.
- Cobertura por tipo de plano y perfil.
- Discrepancias entre score automático y decisión humana.
- Versiones del dataset y métricas por versión.
- Fecha y métricas de cada entrenamiento local futuro.
