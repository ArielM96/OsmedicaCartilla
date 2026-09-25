# OSMEDICA Cartilla API

Proyecto para construir una API propia sobre la cartilla pública de OSMEDICA, con datos normalizados, mejores filtros, búsquedas más útiles y una experiencia preparada para productos web, mobile y asistentes.

## Objetivo

Crear una capa propia sobre la fuente pública actual para:

- normalizar taxonomías y ubicaciones
- mejorar búsqueda y relevancia
- exponer filtros consistentes
- desacoplar el producto del frontend original
- operar bajo dominio propio

## Estado actual

- relevamiento inicial completado
- dataset base recolectado desde WordPress REST API pública
- sincronización automática diaria: `scripts/sync_cartilla.sh` → `research/discover.py` (cron **04:15**)
- contacto enriquecido: dirección, teléfonos y Google Maps desde el listado FacetWP (54 páginas) + fallback REST
- API FastAPI operativa con dataset local
- despliegue aislado en `127.0.0.1:8012`
- publicación pública en `https://cartilla.osmedicaafiliaciones.com/`
- `cartilla.plcommsdash.site` redirige con 301 al dominio nuevo

## Estructura

- `docs/` → PRD, arquitectura, contratos y decisiones
- `research/` → datasets y análisis inicial
- `backend/` → implementación de la API
- `deploy/` → referencia de systemd y Nginx

## Fuente pública detectada

- `https://osmedica.com.ar/wp-json/wp/v2/cartilla`
- `https://osmedica.com.ar/wp-json/wp/v2/tipo_de_prestador`
- `https://osmedica.com.ar/wp-json/wp/v2/provincia`
- `https://osmedica.com.ar/wp-json/wp/v2/especialidades`
- `https://osmedica.com.ar/wp-json/wp/v2/estudios`
- `https://osmedica.com.ar/wp-json/wp/v2/tipo_de_guardia`

## Sincronización

```bash
/opt/dash/OsmedicaCartilla/scripts/sync_cartilla.sh
```

Ejecuta `research/discover.py` (WordPress REST + listado FacetWP paginado), escribe los JSON en `research/` y reinicia `osmedica-cartilla`.

### Cron diario (servidor)

```bash
sudo cp /opt/dash/OsmedicaCartilla/deploy/osmedica-cartilla-sync.cron /etc/cron.d/osmedica-cartilla-sync
sudo chmod 644 /etc/cron.d/osmedica-cartilla-sync
```

Horario: **04:15** todos los días (usuario `root`). Log: `/var/log/osmedica-cartilla/sync.log`.

## URL pública actual

- `https://cartilla.osmedicaafiliaciones.com/`
- `https://cartilla.osmedicaafiliaciones.com/api/v1/health`
- `https://cartilla.osmedicaafiliaciones.com/api/v1/prestadores`

Nginx: `deploy/nginx.cartilla.osmedicaafiliaciones.com.conf` (proxy a `127.0.0.1:8012`) y `deploy/nginx.cartilla.plcommsdash.site.redirect.conf` (redirección 301 desde el dominio anterior). `deploy/nginx.cartilla-api.conf` es la configuración legacy de la ruta `/cartilla-api/`.

## Aislamiento de seguridad

- la API no usa PostgreSQL
- la API no lee nada de las bases ni servicios de `plcommsdash`
- los datos salen únicamente de archivos dentro de `research/`
- el servicio escucha sólo en `127.0.0.1`
- Nginx expone el servicio únicamente vía `cartilla.osmedicaafiliaciones.com`
