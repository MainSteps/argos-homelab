# Monitoreo con Uptime Kuma

**Contenedor:** `argos-kuma` (Uptime Kuma 2.5.6, Docker Compose en `/opt/argos-data/uptime-kuma`) · **Panel:** `http://<IP_LAN>:3001` y `http://<IP_TAILSCALE>:3001` · **Página de estado:** `/status/argos`

`argos-alerta` sigue revisando cada 30 min. Uptime Kuma agrega revisión por minuto, historial de 90 días, una página de estado y la detección de **tareas que no corrieron**. Las alertas llegan al mismo tema de ntfy.

## Cómo está montado

| Aspecto | Decisión |
|---|---|
| Red | Puerto 3001 ligado **solo** a la IP LAN y a la IP de Tailscale, nunca a `0.0.0.0`. No hay redirección de puertos en el router, así que no queda expuesto a Internet. |
| Arranque | `restart: unless-stopped`; `docker.service` arranca después de `tailscaled` y `net.ipv4.ip_nonlocal_bind=1` deja publicar el puerto aunque la IP de Tailscale todavía no exista. |
| Recursos | `mem_limit: 512m`, `cpus: 1.0`, logs rotados (3 × 10 MB). Usa ~100 MB en reposo. |
| Docker | `/var/run/docker.sock` montado **read-only** para los monitores de contenedor. |
| Datos | `./data` (SQLite). Antes de cada respaldo, `argos-backup.sh` hace `sqlite3 .backup` a `kuma-respaldo.db` para tener una copia consistente; restic ya cubre `/opt`. |
| Hora | `TZ=America/Santiago` en el contenedor y en los ajustes. |
| Retención | 90 días de historial. |
| Secretos | Admin en `/etc/argos/uptime-kuma-admin`, tokens push en `/etc/argos/uptime-kuma-push.env`, tema ntfy en `/etc/argos/ntfy-topic` (todos root 600). |

La configuración se hace por API (socket.io) con [`configurar.py`](../scripts/uptime-kuma/configurar.py) (librería `uptime-kuma-api` en un venv, con parches para Kuma 2.x). Es repetible: crea lo que falta y actualiza lo existente por nombre. [`verificar.py`](../scripts/uptime-kuma/verificar.py) lista el estado de cada monitor y manda una notificación de prueba.

## Monitores

Todos avisan por la notificación por defecto **ntfy ArgOS** (prioridad 5 = máxima) y tienen reintentos para evitar falsas alarmas.

| Grupo | Monitor | Tipo | Intervalo |
|---|---|---|---|
| Sistema | SSH (puerto 22) | TCP | 60 s |
| Sistema | Recursos (disco, temperatura, RAM) | push desde sonda | 60 s (cae si disco ≥ 90 %, CPU ≥ 90 °C o RAM libre < 5 %; el "tiempo de respuesta" grafica la temperatura) |
| Sistema | Revisión argos-alerta | push (hook) | espera ≤ 65 min |
| Servicios | Ollama (IA local) | push desde sonda | 60 s (Ollama solo escucha en 127.0.0.1) |
| Servicios | Obsidian Sync | push desde sonda | 60 s |
| Servicios | Docker: Uptime Kuma | contenedor | 5 min |
| Servicios | Oracle (argos-db) | contenedor, **pausado y sin aviso** | — es a demanda; apagado no es falla |
| Tareas programadas | Respaldo restic (03:30), Transcripción (00:30) | push (hook) | espera ≤ 26 h |
| Tareas programadas | Puente, Bandeja (30 min) | push (hook) | espera ≤ 65 min |
| Tareas programadas | Estudio, Índice de búsqueda (cada hora) | push (hook) | espera ≤ 125 min |
| Red | Router (puerta de enlace) | ping | 60 s |
| Red | Internet (1.1.1.1) | ping | 60 s |
| Red | DNS (google.com vía 1.1.1.1) | DNS | 120 s |
| Red | ntfy.sh (canal de alertas) | palabra clave + certificado TLS | 5 min |
| Red | Tailscale conectado | push desde sonda | 60 s |

Router + Internet + DNS separan "se cayó la red de la casa" de "se cayó internet" de "falla solo el DNS". No hay certificados propios que vigilar (todo es HTTP dentro de LAN/Tailscale); se vigila el de ntfy.sh porque de él depende el aviso.

**Ventana de mantenimiento:** todos los días de 03:25 a 04:30 se silencian Internet, DNS y ntfy.sh, porque el respaldo satura la subida.

## Tareas programadas (push)

Cada tarea tiene un drop-in `/etc/systemd/system/argos-<tarea>.service.d/kuma.conf`:

```ini
[Service]
ExecStartPost=+/usr/local/bin/argos-kuma-push <CLAVE> "argos-<tarea> OK"
```

`ExecStartPost` solo corre si `ExecStart` terminó bien, así que el push significa "corrida exitosa". Si falla o no corre, Kuma no recibe nada y avisa cuando vence el plazo. [`argos-kuma-push`](../scripts/uptime-kuma/argos-kuma-push) lee el token del archivo de secretos y nunca hace fallar la unidad.

[`argos-kuma-sondas`](../scripts/uptime-kuma/argos-kuma-sondas) (`argos-kuma-sondas.timer`, cada minuto) revisa lo que el contenedor no ve: Ollama, Obsidian Sync, Tailscale y recursos.

## Aviso externo si ArgOS se apaga

Si ArgOS se apaga, Kuma se apaga con él. Para cubrirlo, sin cuentas nuevas y gratis:

Aviso externo con **Healthchecks.io** (plan gratis): `argos-kuma-sondas` llama cada minuto a la URL de ping guardada en `/etc/argos/latido-externo-url` (root 600). El check `ArgOS` tiene periodo 5 min y gracia 5 min; si falta el latido, Healthchecks avisa por ntfy (prioridad máxima) y por correo.

> Se descartó el vigilante con GitHub Actions (cron poco puntual y se desactiva tras 60 días sin actividad).

## Operación

```bash
cd /opt/argos-data/uptime-kuma && sudo docker compose pull && sudo docker compose up -d   # actualizar
sudo /opt/argos-data/uptime-kuma/venv/bin/python /opt/argos-data/uptime-kuma/configurar.py # reaplicar config
sudo /opt/argos-data/uptime-kuma/venv/bin/python /opt/argos-data/uptime-kuma/verificar.py  # estado + prueba ntfy
```

En el iPhone: abrir el panel en Safari (con Tailscale activo fuera de casa) → Compartir → **Agregar a pantalla de inicio**.
