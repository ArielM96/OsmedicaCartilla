# OSMEDICA Cartilla API

API pública y aislada para consultar la cartilla de OSMEDICA sin depender de bases ni servicios de `plcommsdash`.

## Aislamiento

- lee solamente archivos dentro de `research/`
- no usa PostgreSQL ni variables del entorno de otros proyectos
- escucha en `127.0.0.1:8012`
- sincronización diaria: `scripts/sync_cartilla.sh` → `research/discover.py` (cron **04:15**, ver `deploy/osmedica-cartilla-sync.cron`)
- Nginx lo expone en `https://cartilla.osmedicaafiliaciones.com/`

## Endpoints públicos

- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/prestadores`
- `GET /api/v1/prestadores/{id-o-slug}`
- `GET /api/v1/catalogos/tipos-prestador`
- `GET /api/v1/catalogos/tipos-guardia`
- `GET /api/v1/catalogos/especialidades`
- `GET /api/v1/catalogos/estudios`
- `GET /api/v1/catalogos/regiones`
- `GET /api/v1/catalogos/localidades`
- `GET /api/v1/busqueda/sugerencias`

## Desarrollo local

```bash
cd /opt/dash/OsmedicaCartilla
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 127.0.0.1 --port 8012
```

## Fuente de datos

- `research/cartilla.normalized.json`

La API se construye en memoria al arrancar, así que cualquier actualización del dataset requiere reiniciar el servicio para reflejar cambios.
