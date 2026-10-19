# Monitoreo y estado

**Script:** `argos-estado` · **Datos:** `/var/lib/argos/<servicio>-status`

## Qué hace

Cada servicio escribe una línea de estado al terminar (`OK|FAIL|RUNNING ... métricas`). `argos-estado` las junta en una tabla de colores sin IA:

```text
SERVICIO   ESTADO      EDAD  DETALLE
backup     OK         21.0h  OK 2026-10-18T03:34:37-03:00
busqueda   OK          1.0h  OK ... archivos=220 fragmentos=1982 reindexados=1 ...
transcribir OK         0.1h  OK ... pendientes=0 hechos=1 modelo=turbo
...
Todo OK
```

## Reglas

- Hay alerta si el estado no es `OK`, `RUNNING` o `UP`, si el estado tiene más de 24 h (30 h para la transcripción, que corre una vez por noche) o si falta el archivo de un servicio esperado.
- La fila de límites de potencia es **INFO** y no cuenta como alerta.

## Límites de potencia (`argos-powercap`)

Hay un servicio que fija PL1 = 35 W y PL2 = 50 W vía RAPL al arrancar. **Hoy está desactivado** y el equipo usa los valores de fábrica.

## Pendiente

- Notificaciones activas (hoy el estado se consulta a mano).
