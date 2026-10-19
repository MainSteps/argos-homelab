# Bandeja: clasificación automática de archivos

**Scripts:** `argos-puente.sh`, `argos-bandeja` · **Unidades:** `argos-puente.timer` (cada 30 min), `argos-bandeja.timer` (:10 y :40)

## Qué hace

Subo cualquier archivo a una carpeta `00 Bandeja` en Google Drive (desde el celular o el PC). ArgOS lo lee, decide a qué ramo y tipo pertenece (`Clases`, `Entregas`, `Evaluaciones`) y lo mueve en Drive a `Universidad/<semestre>/<ramo>/<tipo>`.

## Cómo funciona

1. **Puente** (`rclone copy`): copia la carpeta de trabajo de Drive a `/opt/argos-data/puente`. Solo agrega o actualiza; nunca borra. Exporta Google Docs/Sheets/Slides a formatos Office. Un `flock` evita dos copias simultáneas.
2. **Extracción de texto**: primeras páginas del PDF (`pdftotext`), Office con `markitdown`, imágenes con Tesseract.
3. **Capa 1 – reglas**: puntúa palabras clave por ramo (el nombre del archivo pesa x3; la sigla del ramo es decisiva). Si el ganador duplica al segundo, clasifica sin IA.
4. **Capa 2 – IA local (qwen3:4b)**: solo si las reglas dudan. Respuesta con JSON Schema forzado. Se mueve **solo si se cumplen 3 señales**:
   - dos preguntas con las etiquetas en orden distinto dan la misma respuesta,
   - el modelo no declara seguridad "baja",
   - hay al menos una palabra clave de esa etiqueta en el nombre o el texto.
5. Si no, el archivo **queda en espera** en `00 Bandeja` y queda registrado en el log.
6. Antes de mover comprueba que el archivo siga en Drive y que no exista ya en el destino (no sobrescribe).

## Decisiones técnicas

- **Reglas antes que IA**: rápido, explicable y no gasta CPU en lo obvio.
- **Doble pregunta con orden invertido** para detectar respuestas al azar de un modelo chico.
- **Cede la CPU a la transcripción**: si `argos-transcribir` tiene su lock, la capa IA se omite y lo dudoso espera.
- Dry-run por defecto; el timer usa `--aplicar`.

## Límites conocidos

- Las palabras clave por ramo se mantienen a mano cada semestre.
- Un modelo de 4B puede equivocarse; por eso lo dudoso nunca se mueve.
