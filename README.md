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
