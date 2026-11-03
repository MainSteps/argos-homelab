# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [1.0.0] - 2026-11-03

### Agregado
- Guía [Cómo montar el tuyo](docs/00-replicar.md): requisitos, instalación, marcadores y verificación.
- Capturas reales de ArgOS en `docs/img/` y sección "Vista rápida" en el README.
- `CONTRIBUTING.md`, `SECURITY.md` y plantillas de issues; configuración de ruff (`ruff.toml`).

### Cambiado
- README con las cifras actuales del índice (235 notas, 2.132 fragmentos).
- Se quitaron imports sin uso en `argos-estudio`, `argos-transcribir` y `configurar.py` (sin cambios de lógica).
- El correo de destino de `argos-alerta` pasó a ser un marcador.

## Historial previo (19 al 22 de octubre de 2026)
- 2026-10-22: Uptime Kuma (compose, configuración por API, sondas push), aviso externo con Healthchecks.io, alertas por ntfy y `argos-estado` sin falsas alertas en servicios continuos.
- 2026-10-21: alertas por correo (`argos-alerta`), archivos grandes fuera de Sync, copia de respaldos fuera del equipo y prueba de restauración.
- 2026-10-19: documentación inicial.

[1.0.0]: https://github.com/MainSteps/argos-homelab/releases/tag/v1.0.0
