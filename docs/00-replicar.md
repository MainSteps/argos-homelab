# Cómo montar el tuyo

Guía mínima para levantar una copia de ArgOS en tu propio equipo. Los scripts de `scripts/` son los que corren en mi servidor, **sanitizados**: antes de usarlos tienes que reemplazar los marcadores `<ASÍ>` por tus valores. No es un instalador automático; arma el sistema por partes y verifica cada una.

[← Volver al README](../README.md)

## 1. Requisitos

**Hardware.** ArgOS corre en un i5-10500T (6 núcleos / 12 hilos, 35 W, sin GPU) con 16 GB de RAM y un NVMe de 512 GB. Como referencia de lo que usa:

| Recurso | Uso real en ArgOS |
|---|---|
| Modelos Ollama | `qwen3:4b` ocupa 2,5 GB y `bge-m3` 1,2 GB en disco |
| Disco total usado | 32 GB del sistema completo, con modelos y datos |
| RAM | Con los servicios en reposo se usan ~1,1 GiB; el LLM y Whisper suben ese consumo mientras corren |

Con una CPU de 4 núcleos y 8 GB de RAM puede funcionar, pero no lo he probado: espera tiempos bastante más largos en el LLM y en la transcripción.

**Software** (versiones instaladas hoy en ArgOS):

| Componente | Versión en ArgOS | Lo usa |
|---|---|---|
| Ubuntu | 26.04 LTS | todo |
| Python | 3.14 | scripts en Python |
| Ollama | 0.40.5, con `qwen3:4b` y `bge-m3` | `argos-ia`, `argos-bandeja`, `argos-indexar`, `argos-buscar` |
| rclone | 1.75 | `argos-puente`, `argos-bandeja` (remoto de Google Drive) |
| restic | 0.18 | `argos-backup` |
| faster-whisper | 1.2.1 (modelo `large-v3-turbo`, int8) | `argos-transcribir` |
| obsidian-headless | 0.0.14 (npm, CLI `ob`) | `argos-obsidian` (requiere una suscripción a Obsidian Sync) |
| markitdown + NumPy | 0.1.8 / 2.5 | `argos-estudio`, `argos-md`, índice |
| poppler-utils, tesseract-ocr (+`-spa`), ffmpeg, jq | paquetes de Ubuntu | conversión, OCR, audio, `argos-ia` |
| msmtp | opcional | correo de `argos-alerta` |
| Docker + Compose | opcional | Uptime Kuma |

## 2. Instalar dependencias

```bash
sudo apt install python3-venv poppler-utils tesseract-ocr tesseract-ocr-spa ffmpeg jq rclone restic nodejs npm
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b
ollama pull bge-m3

# Entornos de Python: las rutas están fijadas en el shebang de los scripts
sudo python3 -m venv /opt/argos-ia/venv
sudo /opt/argos-ia/venv/bin/pip install markitdown numpy
sudo python3 -m venv /opt/argos-transcribir/venv
sudo /opt/argos-transcribir/venv/bin/pip install faster-whisper numpy

# Opcional: Obsidian Sync headless
sudo npm install -g obsidian-headless
```

El paquete `rclone` de tu distribución puede estar desactualizado. Si tienes problemas con Google Drive, instala la versión oficial desde rclone.org.

## 3. Copiar scripts y unidades

```bash
git clone https://github.com/MainSteps/argos-homelab.git && cd argos-homelab
sudo install -m 755 scripts/bin/* /usr/local/bin/
sudo install -m 644 scripts/systemd/* /etc/systemd/system/
sudo mkdir -p /etc/argos /var/lib/argos /var/log/argos /opt/argos-data
```

Las unidades buscan los scripts en `/usr/local/bin` con su nombre exacto (incluidos `argos-puente.sh`, `argos-backup.sh` y `argos-powercap.sh`).

Después busca y reemplaza los marcadores:

```bash
grep -rn '<[A-Z_]*>' /usr/local/bin/argos-* /etc/systemd/system/argos-*
```

| Marcador | Qué poner |
|---|---|
| `<USUARIO>` | Tu usuario de Linux (el que corre los servicios) |
| `<RUTA_BOVEDA>` | Ruta absoluta de tu bóveda de Obsidian |
| `<REMOTO_RCLONE>` / `<CARPETA_DRIVE>` | Remoto que creaste con `rclone config` y carpeta de Drive a copiar |
| `<SEMESTRE>` | Subcarpeta de material dentro de la copia local |
| `<CORREO_DESTINO>` | Dónde recibir las alertas (o define `ARGOS_ALERTA_PARA`) |

Los marcadores de `scripts/uptime-kuma/` (`<IP_LAN>`, `<IP_TAILSCALE>`, `<CLAVE>`) se explican en [10-uptime-kuma.md](10-uptime-kuma.md).

Ajusta también las listas de ramos y palabras clave de `argos-bandeja` y el mapa de carpetas de `argos-estudio`: están pensadas para mi carrera.

## 4. Configurar los `.example`

```bash
sudo install -m 600 scripts/config/restic.env.example /etc/argos/restic.env   # repositorio, clave y host
sudo install -m 600 scripts/config/msmtprc.example /etc/argos/msmtprc          # opcional: correo
rclone config                                                                 # como <USUARIO>: crea el remoto de Drive
restic init                                                                   # con las variables de restic.env cargadas
```

Nunca subas estos archivos reales a un repositorio. Sin `/etc/argos/msmtprc`, `argos-alerta` solo simula el envío; para usar ntfy, pon tu tema en `/etc/argos/ntfy-topic` (ver [alertas](09-alertas.md)).

## 5. Habilitar los timers

Empieza por lo que no depende de nada y prueba a mano antes de automatizar:

```bash
sudo systemctl daemon-reload
sudo systemctl start argos-puente.service && argos-estado     # ¿llegó la copia de Drive?
sudo systemctl enable --now argos-puente.timer argos-bandeja.timer argos-estudio.timer \
  argos-busqueda.timer argos-transcribir.timer argos-backup.timer argos-alerta.timer
sudo systemctl enable --now argos-obsidian.service             # solo si usas Obsidian Sync
```

`argos-powercap.service` es opcional: fija límites de potencia para un i5-10500T. Revisa los valores antes de activarlo en otra CPU.

## 6. Verificar

```bash
systemctl list-timers 'argos-*'
argos-estado
argos-buscar "una pregunta sobre tus notas"
```

`argos-estado` lee los archivos `/var/lib/argos/*-status`. Cada servicio debería pasar a `OK` después de su primera ejecución. Si uno queda en `FAIL`, revisa `journalctl -u argos-<servicio>` y su log en `/var/log/argos/`.

## 7. Opcional: monitoreo

Uptime Kuma corre en Docker con `scripts/uptime-kuma/compose.yaml` y avisa por ntfy. Los pasos están en [10-uptime-kuma.md](10-uptime-kuma.md).
