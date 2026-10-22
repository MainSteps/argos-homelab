# Sync de la bóveda (Obsidian headless)

**Unidad:** `argos-obsidian.service` (continuo, `Restart=always`)

## Qué hace

Mantiene en ArgOS una copia de la bóveda de Obsidian sincronizada con mis otros dispositivos usando **Obsidian Sync** en modo headless (CLI `ob sync --continuous`), sin interfaz gráfica.

Así los servicios de ArgOS escriben notas (material, transcripciones, mapa) que aparecen solas en el PC y el celular, y lo que escribo yo queda disponible para el índice.

## Cómo funciona

- Servicio systemd que corre con un usuario sin privilegios y se reinicia a los 30 s si falla.
- `ExecStartPost` y `ExecStopPost` escriben `RUNNING` o `STOPPED result=...` en `obsidian-status` para que `argos-estado` lo muestre.

## Límites conocidos

- **5 MB por archivo** en el plan actual de Obsidian Sync: los PDFs más pesados no se sincronizan y se quedan solo en el dispositivo de origen. Se llevan por fuera: `pdfs_grandes.py --empaquetar` en el PC, copia a ArgOS y `verificar_pdfs_grandes.py` (repo material-u3). El 21-10-2026 quedaron 28 archivos de más de 5 MiB en ArgOS, verificados (OK=11 por hash; 17 ya estaban en ArgOS).
- Si dos dispositivos editan la misma nota a la vez, se aplica la resolución de conflictos de Obsidian Sync.

## Archivos grandes y verificación

- Inventario y comparación PC ↔ ArgOS: `herramientas/inventario.py` y `comparar_inventarios.py` (material-u3, PR #14).
- Archivos de más de 5 MiB: `herramientas/pdfs_grandes.py` y `verificar_pdfs_grandes.py` (PR #13).
- Auditoría de enlaces y jerarquía (solo lectura): `herramientas/auditar_enlaces.py` y `jerarquia.py`. Resultado del 21-10-2026: 0 enlaces rotos, 0 notas huérfanas, 0 adjuntos sin enlace.

## Configuración de Obsidian

Se gestiona desde ArgOS con `herramientas/config_obsidian.py BOVEDA [--aplicar]` (sin `--aplicar` es dry-run; hace merge con lo existente). Solo complementos principales, ninguno de la comunidad.

- **Core plugins:** backlinks, enlaces salientes, etiquetas, propiedades, marcadores, esquema, canvas, plantillas (`_Sistema/Plantillas`), notas diarias (`_Sistema/Diario`), vista previa, recuperación de archivos, conteo de palabras, grafo, búsqueda, paleta de comandos, comandos `/`, notas al pie y Bases.
- **app.json:** wikilinks con formato más corto, actualizar enlaces al mover, adjuntos en `./_adjuntos`, propiedades visibles, ancho de lectura, papelera local `.trash`, `_Sistema/Papelera` excluida de búsqueda y grafo.
- **Apariencia:** tema oscuro base y snippet propio `snippets/argos.css` (colores por ramo iguales a `graph.json`).
- **Navegación:** `bookmarks.json` (Inicio, Mapa, Base, Canvas y un índice por ramo), `_Sistema/Notas por ramo.base` (tabla con vistas por ramo) y `_Sistema/Mapa.canvas` (Inicio → ramos → unidades).

**Ojo:** el modo continuo de `ob` no detecta cambios hechos directamente en `.obsidian/` en ArgOS; después de escribir configuración hay que reiniciar `argos-obsidian` para que la suba.
