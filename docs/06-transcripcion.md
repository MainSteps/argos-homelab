# Transcripción de clases

**Script:** `argos-transcribir` · **Unidad:** `argos-transcribir.timer` (00:30 diario, `TimeoutStartSec=6h`)

## Qué hace

Grabo la clase con el celular y subo el audio a la carpeta `Grabaciones` del ramo en Drive. De noche, ArgOS lo transcribe y crea en la bóveda la nota `Clase AAAA-MM-DD HHMM - <Ramo>.md`, con frontmatter (fecha, duración, modelo) y la transcripción en bloques de ~45 s con marca de tiempo.

## Cómo funciona

- **faster-whisper `large-v3-turbo`, int8, en CPU**, idioma español, con filtro VAD para saltar silencios y `beam_size=5`. Usa 6 hilos.
- `ffmpeg` decodifica cualquier formato común (m4a, mp3, ogg, opus, wav, webm, flac...) a PCM de 16 kHz.
- La fecha de la clase se toma de los metadatos del audio (`ffprobe`) o, si no hay, de la fecha del archivo.
- Lleva el estado por sha256 en `hechos.json`, con la duración, el tiempo, el RTF y la temperatura máxima de cada audio.
- **Nunca borra ni mueve el audio original.** El modelo se carga en modo offline (`HF_HUB_OFFLINE=1`).

## Decisiones técnicas

- **Protección térmica**: si la CPU llega a 82 °C, se pausa en tramos de 20 s.
- **Convivencia**: si la IA local está generando, espera a la próxima vuelta. Mientras transcribe tiene un lock que la bandeja respeta.
- **Corte a las 03:00**: no empieza audios nuevos después de esa hora, para no chocar con el respaldo de las 03:30.
- Sin resumen automático: la transcripción es la fuente y el resumen se pide aparte.

## En desarrollo

- Una nueva versión con listas de términos por ramo (para mejorar nombres técnicos), pruebas automatizadas y un instalador reproducible. *Pendiente de instalar.*

## Límites conocidos

- Puede equivocarse en nombres propios, fórmulas y números; la nota lo advierte.
- Va más lento que el tiempo real en clases largas en esta CPU, así que solo corre de noche.
