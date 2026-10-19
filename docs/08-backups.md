# Backups

**Script:** `argos-backup.sh` · **Unidad:** `argos-backup.timer` (03:30 diario, `Persistent=true`, hasta 5 min de retraso aleatorio)

## Qué hace

Respaldo diario con **restic** de la configuración del sistema, el home del usuario, los datos de `/opt` (incluye la bóveda, los índices y los venvs) y los volúmenes de Docker. Se excluyen las cachés.

## Cómo funciona

1. `restic backup` con etiqueta y host fijos.
2. Retención: `--keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune`.
3. `restic check` **una vez por semana ISO** (recuerda cuál fue la última semana verificada).
4. Escribe `OK` o `FAIL <etapa>` en `backup-status`.

Corre con `Nice=10` e `IOSchedulingClass=idle` para no molestar.

## Configuración

Las credenciales del repositorio restic están en `/etc/argos/restic.env` (solo root). En este repo solo hay un ejemplo: [`scripts/config/restic.env.example`](../scripts/config/restic.env.example).

## Pendiente

- **Copia fuera del equipo (regla 3-2-1):** no está verificada. Está en el roadmap.
- Una prueba de restauración documentada.
