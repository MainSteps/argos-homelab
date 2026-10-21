# Alertas por correo

**Script:** `argos-alerta` · **Unidad:** `argos-alerta.timer` (cada 30 min, en los minutos 07 y 37)

## Qué revisa

- Las alertas de `argos-estado`. Que Oracle esté apagado a demanda **no** cuenta como alerta, y tampoco la edad del estado de `ia`, que corre solo a demanda.
- Unidades de systemd fallidas, salvo `fwupd-refresh.service`, que falla sola y solo mete ruido.
- Disco al 90 % o más en `/` y `/opt`.
- Temperatura de 90 °C o más en cualquier zona térmica.

## Cuándo avisa

Guarda las alertas activas en `/var/lib/argos/alerta.json` y manda un correo **solo cuando eso cambia**: una alerta nueva o una que se resolvió. Cuando todo vuelve a la normalidad, manda un correo de "Recuperado". Si el envío falla, borra el estado para reintentar en la próxima revisión.

No usa IA ni servicios pagados.

## Envío

Usa `msmtp` con `/etc/argos/msmtprc` (root:root, 600) y la cuenta de Gmail con una **clave de aplicación** guardada en `/etc/argos/gmail-app-password` (root:root, 600). Hay una plantilla en [`scripts/config/msmtprc.example`](../scripts/config/msmtprc.example).

Si `/etc/argos/msmtprc` no existe, o si se corre con `--simular`, solo imprime el correo en el journal (`journalctl -u argos-alerta`).

## Probar sin tocar el estado real

```bash
cp -r /var/lib/argos /tmp/st && echo "FAIL $(date -Is) prueba" > /tmp/st/backup-status
ARGOS_STATUS_DIR=/tmp/st ARGOS_ALERTA_ESTADO=/tmp/al.json argos-alerta --simular
```
