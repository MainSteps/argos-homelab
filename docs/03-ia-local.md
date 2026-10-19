# IA local

**Scripts:** `argos-ia`, `argos-md` · **Motor:** Ollama (API local en `127.0.0.1:11434`)

## Modelos instalados

| Modelo | Uso |
|---|---|
| `qwen3:4b` | Modelo por defecto: clasificación de la bandeja y tareas de texto con `argos-ia` |
| `qwen3:1.7b` | Alternativa más liviana |
| `bge-m3` | Embeddings para la búsqueda semántica |

## `argos-ia`

```text
argos-ia [-m modelo] "<instrucción>" [archivo]
```

Extrae el texto del archivo (PDF, Office o texto plano), lo junta con la instrucción, consulta a Ollama y guarda el resultado como `.md` con los tokens/s. Escribe su estado en `ia-status`.

`argos-md <archivo>` solo convierte un archivo a Markdown con markitdown.

## Decisiones técnicas

- **Sin razonamiento visible**: `qwen3:4b` (versión 2507) ignora `think:false` y `/no_think`, así que se combinan cuatro capas: `think:false`, un mensaje de sistema, una respuesta pre-iniciada con `stop` en `<think>` y, como último recurso, se limpian los bloques `<think>`.
- **Medido, no supuesto**: prueba de 15 minutos a carga sostenida con ~12 tokens/s, sin reinicios y con una temperatura máxima de 72 °C.

## Límites conocidos

- **Modelos de 8B bloqueados**: el script los rechaza porque son demasiado lentos en esta CPU, y el equipo tiene problemas térmicos (pasta térmica seca).
- Sin GPU. Un modelo de 4B sirve para clasificar y resumir, no para razonar en profundidad.
