# Seguridad

## Reportar un problema

Si encuentras un secreto expuesto o una vulnerabilidad en los scripts, **no abras un issue público**. Repórtalo con [un aviso privado de seguridad](https://github.com/MainSteps/argos-homelab/security/advisories/new). Respondo apenas pueda; es un proyecto personal y no hay un plazo garantizado.

## Qué se excluyó del repositorio

- Credenciales: claves de restic, rclone, Obsidian Sync, Gmail/msmtp, ntfy, Uptime Kuma y Healthchecks. Solo se publican plantillas `.example`.
- Direcciones de red (LAN, Tailscale e IP pública), el usuario de Linux y el correo personal: se reemplazaron por marcadores `<ASÍ>`.
- Contenido de la bóveda: notas, apuntes, grabaciones y material de clases.

## Cómo está protegido el servidor

- Los secretos viven en `/etc/argos/` con permisos `600`.
- El panel de Uptime Kuma escucha solo en la LAN y en Tailscale, nunca en `0.0.0.0`.
- El acceso remoto es por SSH con llave a través de Tailscale.
