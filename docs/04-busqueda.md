# Búsqueda semántica en la bóveda

**Scripts:** `argos-mapa`, `argos-indexar`, `argos-buscar` · **Unidad:** `argos-busqueda.timer` (:35 cada hora, después de estudio)

## Qué hace

Permite preguntar en lenguaje natural ("¿cómo se normaliza una tabla?") y obtener los fragmentos más relevantes de mis notas, en un formato compacto para pasárselo a un asistente.

## Cómo funciona

1. **`argos-mapa`** genera `_Sistema/Mapa.md`: el árbol de la bóveda con una descripción de una línea y los tokens aproximados de cada nota. Sirve para que un asistente sepa qué existe sin leerlo todo.
2. **`argos-indexar`** divide cada nota por encabezados (fragmentos de ~200 a 1.800 caracteres), calcula embeddings con `bge-m3` vía Ollama y los guarda en SQLite junto con un índice de texto completo FTS5 (sin tildes). Es incremental: solo reindexa las notas cuyo sha256 o modelo cambió, y borra del índice las notas eliminadas.
3. **`argos-buscar`** hace una **búsqueda híbrida**: similitud coseno (NumPy) más un bono pequeño para los 30 mejores resultados por palabra clave (BM25). Se puede filtrar por ramo (`-r`) o excluir el material crudo (`--sin-material`), y la salida puede ser texto o `--json`.

```text
argos-buscar "integridad referencial" -r "base de datos" -k 5
```

## Decisiones técnicas

- **SQLite + NumPy en vez de una base vectorial**: con unos 2.000 fragmentos, la fuerza bruta tarda milisegundos y no hay que mantener ningún servicio aparte.
- **Aviso anti-alucinación**: si la mejor similitud es menor que 0,45, avisa que probablemente el tema no está en la bóveda.
- Los metadatos del frontmatter (ramo, tipo, unidad) se guardan con cada fragmento para poder filtrar.

## Estado

Unas 220 notas indexadas en unos 2.000 fragmentos. Una pasada incremental típica tarda unos 25 s.
