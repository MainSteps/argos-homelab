# Estudio: material de clases → notas Markdown

**Script:** `argos-estudio` · **Unidad:** `argos-estudio.timer` (:25 cada hora)

## Qué hace

Recorre la copia local del semestre y convierte cada PDF, DOCX, PPTX y XLSX nuevo en una nota `.md` dentro de la bóveda, en `Ramos/<ramo>/Material/...`, respetando la estructura de carpetas. **No usa IA.**

## Cómo funciona

- PDF con texto → `pdftotext -layout`. PDF escaneado → OCR (`pdftoppm` 200 dpi + Tesseract `spa+eng`). Office → `markitdown`.
- Cada nota lleva frontmatter con la fuente, el ramo, la fecha de conversión, el sha256 del original y enlaces de navegación al ramo.
- Un índice JSON guarda `sha256 del original → nota generada → sha256 de la nota generada`.

## Decisiones técnicas

- **Idempotente**: si el original no cambió, se salta.
- **Nunca pisa ediciones**: si la nota fue modificada a mano (su hash no coincide con el generado), escribe una versión nueva `(v2)`.
- **Sin duplicados**: si el mismo original (mismo sha256) ya fue importado a mano en una carpeta `Fuentes/` de la bóveda, no lo convierte otra vez. Los hashes de `Fuentes/` se cachean por tamaño + fecha.
- Si el OCR no logra leer, la nota queda marcada `estado: pendiente OCR` y se reintenta.

## Límites conocidos

- La calidad del OCR depende del escaneo; las notas OCR llevan un aviso para revisar errores.
- Fórmulas y tablas complejas pierden formato en la conversión.
