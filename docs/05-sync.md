# Sync de la bóveda (Obsidian headless)

**Unidad:** `argos-obsidian.service` (continuo, `Restart=always`)

## Qué hace

Mantiene en ArgOS una copia de la bóveda de Obsidian sincronizada con mis otros dispositivos usando **Obsidian Sync** en modo headless (CLI `ob sync --continuous`), sin interfaz gráfica.

Así los servicios de ArgOS escriben notas (material, transcripciones, mapa) que aparecen solas en el PC y el celular, y lo que escribo yo queda disponible para el índice.

## Cómo funciona

- Servicio systemd que corre con un usuario sin privilegios y se reinicia a los 30 s si falla.
- `ExecStartPost` y `ExecStopPost` escriben `RUNNING` o `STOPPED result=...` en `obsidian-status` para que `argos-estado` lo muestre.

## Límites conocidos

- **5 MB por archivo** en el plan actual de Obsidian Sync: los PDFs más pesados no se sincronizan y se quedan solo en el dispositivo de origen. Está pendiente llevarlos por otro camino con verificación sha256 (ver el roadmap).
- Si dos dispositivos editan la misma nota a la vez, se aplica la resolución de conflictos de Obsidian Sync.
