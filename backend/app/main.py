from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import BASE_DIR, MAP_CACHE_PATH
from .data import get_store
from .maps import LocationGeocoder
from .schemas import (
    CatalogItem,
    PrestadorItem,
    PrestadorListResponse,
    SuggestionsResponse,
)


app = FastAPI(
    title="OSMEDICA Cartilla API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

INDEX_FILE = BASE_DIR / "backend" / "app" / "static" / "index.html"
FAVICON_FILE = BASE_DIR / "backend" / "app" / "static" / "favicon.svg"
LOGO_FILE = BASE_DIR / "backend" / "app" / "static" / "osmedica-logo-horizontal.png"
geocoder = LocationGeocoder(MAP_CACHE_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/favicon.svg")
def favicon_svg() -> FileResponse:
    return FileResponse(FAVICON_FILE, media_type="image/svg+xml")


@app.get("/favicon.ico")
def favicon_ico() -> FileResponse:
    return FileResponse(FAVICON_FILE, media_type="image/svg+xml")


@app.get("/osmedica-logo-horizontal.png")
def osmedica_logo() -> FileResponse:
    return FileResponse(LOGO_FILE, media_type="image/png")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/prestadores", response_model=PrestadorListResponse)
def list_prestadores(
    q: str | None = Query(default=None, max_length=100),
    tipoPrestador: str | None = Query(default=None),
    especialidad: str | None = Query(default=None),
    estudio: str | None = Query(default=None),
    region: str | None = Query(default=None),
    localidad: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    includeFacets: bool = Query(default=False),
) -> dict:
    return get_store().list_prestadores(
        q=q,
        tipo_prestador=tipoPrestador,
        especialidad=especialidad,
        estudio=estudio,
        region=region,
        localidad=localidad,
        page=page,
        limit=limit,
        include_facets=includeFacets,
    )


@app.get("/api/v1/prestadores/{identifier}", response_model=PrestadorItem)
def get_prestador(identifier: str) -> dict:
    prestador = get_store().get_prestador(identifier)
    if not prestador:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return prestador


@app.get("/api/v1/prestadores/{identifier}/mapa")
def get_prestador_map(identifier: str) -> dict:
    prestador = get_store().get_prestador(identifier)
    if not prestador:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")

    contacto = prestador.get("contacto") or {}
    query = contacto.get("ubicacion") or contacto.get("direccion")
    if not query:
        raise HTTPException(status_code=404, detail="Ubicación no disponible")

    # Some source values include commercial areas such as "GBA Zona Oeste",
    # which are useful to people but are not always understood by geocoders.
    candidates = [f"{query}, Argentina"]
    locality = query.split(",", 1)[0].strip()
    if locality and locality != query:
        candidates.append(f"{locality}, Argentina")

    location = None
    for candidate in candidates:
        if not candidate:
            continue
        location = geocoder.locate(candidate)
        if location:
            break
    if not location:
        raise HTTPException(status_code=404, detail="No pude ubicar este prestador en el mapa")
    return {"location": location, "precision": "aproximada"}


@app.get("/api/v1/catalogos/tipos-prestador", response_model=list[CatalogItem])
def catalog_tipos_prestador() -> list[dict]:
    return get_store().list_catalog("tiposPrestador")


@app.get("/api/v1/catalogos/tipos-guardia", response_model=list[CatalogItem])
def catalog_tipos_guardia() -> list[dict]:
    return get_store().list_catalog("tiposGuardia")


@app.get("/api/v1/catalogos/especialidades", response_model=list[CatalogItem])
def catalog_especialidades() -> list[dict]:
    return get_store().list_catalog("especialidades")


@app.get("/api/v1/catalogos/estudios", response_model=list[CatalogItem])
def catalog_estudios() -> list[dict]:
    return get_store().list_catalog("estudios")


@app.get("/api/v1/catalogos/regiones", response_model=list[CatalogItem])
def catalog_regiones() -> list[dict]:
    return get_store().list_catalog("regiones")


@app.get("/api/v1/catalogos/localidades", response_model=list[CatalogItem])
def catalog_localidades(region: str | None = Query(default=None)) -> list[dict]:
    return get_store().list_catalog("localidades", region=region)


@app.get("/api/v1/busqueda/sugerencias", response_model=SuggestionsResponse)
def search_suggestions(q: str = Query(min_length=1, max_length=100), limit: int = Query(default=10, ge=1, le=20)) -> dict:
    return {"suggestions": get_store().suggestions_for(q, limit)}
