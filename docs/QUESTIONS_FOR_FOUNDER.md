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

## Respuestas cerradas (sesión grill-me, 2026-09-13)

1. **Uso inicial:** interno, para proyectos propios/Flopwork. No se optimiza aún para terceros.
2. **Perfil de vuelo prioritario:** `cinematic_drone_v1` (el usuario vuela el Avata 2 de forma suave; el perfil FPV se calibra más adelante).
3. **NLE prioritario:** DaVinci Resolve primero (FCPXML), Premiere Pro después.
4. **Material real típico:** mezcla de varios drones/formatos aún no estandarizada; el más habitual y de referencia inicial es DJI Avata 2, `.MP4`, H.265/HEVC, 8-bit Normal o 10-bit D-Log M. Fase 1 soporta bien 2-3 formatos propios primero; el resto falla con mensaje claro, no en silencio.
5. **CPU/GPU:** sólo CPU en Fase 1-2. GPU/CUDA se evalúa después con datos reales de rendimiento, no por adelantado.
6. **Offline:** offline por defecto siempre; cloud/modelos descargables opcionales quedan abiertos a futuro con opt-in explícito, no se implementan ahora.
7. **Dataset:** el usuario ya tiene clips reales grabados y listos para usar en validación.
8. **Tamaño de sesión típica:** hasta ~50 clips por lote. Fase 1 debe soportar ese volumen con comodidad.
9. **Duración de segmento:** `minimum_duration_seconds` es sólo un umbral mínimo para descartar candidatos demasiado cortos, no una duración fija de salida. Un segmento fluido de 20 s debe conservarse como 20 s. Se debe ofrecer un modo "auto" (duración natural detectada) además de permitir fijar una duración mínima personalizada.

