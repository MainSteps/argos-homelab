# Contribuir

ArgOS es un proyecto personal, pero las sugerencias son bienvenidas.

- **Dudas o ideas:** abre un issue con la plantilla que corresponda.
- **Errores en scripts o docs:** un issue o un PR pequeño y enfocado en un solo cambio.
- **Antes de un PR:** pasa shellcheck y ruff en local:
  ```bash
  shellcheck -S warning scripts/bin/*.sh scripts/bin/argos-ia scripts/bin/argos-md scripts/uptime-kuma/argos-kuma-*
  ruff check scripts/bin/argos-* scripts/uptime-kuma/*.py
  ```
- **Nada de datos reales:** no incluyas IPs, correos, tokens, rutas personales ni contenido de notas. Usa marcadores `<ASÍ>`.
- Escribe en español.
