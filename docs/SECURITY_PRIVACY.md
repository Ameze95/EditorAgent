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
