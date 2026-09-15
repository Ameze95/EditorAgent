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

## Convención frontend

- La interfaz React se organizará siguiendo Atomic Design: `atoms`, `molecules`, `organisms`, `pages`, `hooks`, `lib/api`, `styles` y `types`.
- Los componentes visuales no accederán directamente a SQLite ni contendrán lógica de análisis o FFmpeg.
- La API local será la frontera entre frontend y backend.
- Los estilos se dividirán por módulo funcional, con tokens compartidos y sin crear un archivo CSS por componente trivial.

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
