# Alertas (ntfy)

**Script:** `argos-alerta` · **Unidad:** `argos-alerta.timer` (cada 30 min, en los minutos 07 y 37)

## Qué revisa

- Las alertas de `argos-estado`. Que Oracle esté apagado a demanda **no** cuenta como alerta, y tampoco la edad del estado de `ia`, que corre solo a demanda.
- Unidades de systemd fallidas, salvo `fwupd-refresh.service`, que falla sola y solo mete ruido.
- Disco al 90 % o más en `/` y `/opt`.
- Temperatura de 90 °C o más en cualquier zona térmica.

## Cuándo avisa

Guarda las alertas activas en `/var/lib/argos/alerta.json` y avisa **solo cuando eso cambia**: una alerta nueva o una que se resolvió. Cuando todo vuelve a la normalidad, avisa "Recuperado". Si el envío falla, borra el estado para reintentar en la próxima revisión.

No usa IA ni servicios pagados.

## Envío

Principal: **ntfy** público (`https://ntfy.sh`). El tema está en `/etc/argos/ntfy-topic` (root:root, 600); es largo y aleatorio porque los temas públicos los lee quien sepa el nombre. El mensaje solo lleva el título y la lista de alertas nuevas o resueltas, nunca el detalle de `argos-estado`. Prioridad alta si hay alertas nuevas.

Respaldo opcional: `msmtp` con `/etc/argos/msmtprc` (plantilla en [`scripts/config/msmtprc.example`](../scripts/config/msmtprc.example)). Hoy no está configurado: Outlook/Hotmail personal ya no acepta SMTP con contraseña simple.

Si no hay ningún medio configurado, o se corre con `--simular`, solo imprime en el journal (`journalctl -u argos-alerta`).

Complementos: **Uptime Kuma** ([10-uptime-kuma.md](10-uptime-kuma.md)) revisa cada minuto y avisa por el mismo tema, y **Healthchecks.io** avisa si ArgOS deja de dar señales (apagado o sin internet).

## Probar sin tocar el estado real

```bash
cp -r /var/lib/argos /tmp/st && echo "FAIL $(date -Is) prueba" > /tmp/st/backup-status
ARGOS_STATUS_DIR=/tmp/st ARGOS_ALERTA_ESTADO=/tmp/al.json argos-alerta --simular
```
