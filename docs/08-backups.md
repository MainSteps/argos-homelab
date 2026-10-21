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

## Copia fuera del equipo

El repositorio restic **no está en el disco de ArgOS**: vive en Google Drive y se accede con el backend `rclone:` de restic (un remoto rclone de Drive configurado solo para root). Así, cada respaldo diario ya es una copia fuera del equipo.

- **Qué cubre:** todo lo de arriba, incluida la bóveda y la carpeta local de respaldos puntuales (`/opt/argos-data/backups`, tarballs que se hacen antes de cambios grandes).
- **Copias locales:** esos tarballs puntuales, en el disco de ArgOS. Las maneja root (`root:root`, 644).
- **Verificado (21/10/2026):** 8 snapshots en el repositorio; el último, de las 03:33, terminó `OK` (unos 4,8 GiB, unos 19 000 archivos).

## Prueba de restauración

Restaurar un archivo del último snapshot en una carpeta temporal y compararlo con el original:

```bash
sudo bash -c '. /etc/argos/restic.env
restic restore latest --target /tmp/rt --include "/opt/UNIVERSIDAD/00 Inicio.md"
cmp "/tmp/rt/opt/UNIVERSIDAD/00 Inicio.md" "/opt/UNIVERSIDAD/00 Inicio.md" && echo OK
rm -rf /tmp/rt'
```

Última prueba: 21/10/2026, archivo idéntico.

Nunca restaurar directamente sobre `/opt`: siempre a una carpeta aparte y copiar a mano lo necesario.

## Pendiente

- Prueba de restauración completa (no solo un archivo).
