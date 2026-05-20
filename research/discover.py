#!/usr/bin/env python3
"""
Sincroniza la cartilla pública de OSMEDICA desde WordPress REST API
y enriquece contacto (dirección, teléfonos, Google Maps) desde el listado HTML.
"""
from __future__ import annotations

import json
import re
import sys
import time
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, unquote, urljoin

import requests

BASE = "https://osmedica.com.ar/wp-json/wp/v2/"
SITE = "https://osmedica.com.ar/"
CARTILLA_URL = f"{SITE}cartilla/"

RESEARCH_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = RESEARCH_DIR / "osmedica-api"

TAXONOMY_ENDPOINTS = [
    "tipo_de_prestador",
    "provincia",
    "especialidades",
    "estudios",
    "tipo_de_guardia",
]

CARTILLA_ENDPOINT = "cartilla"

# Teléfonos del sitio (footer / sedes), no del prestador
SITE_PHONE_PREFIXES = (
    "0800",
    "0113753",
    "0115263",
    "5263",
    "5262",
)

USER_AGENT = "Mozilla/5.0 (compatible; OsmedicaCartillaSync/1.1; +https://plcommsdash.site)"


def strip_html(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    value = unescape(value)
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def clean_phone(raw: str) -> str:
    raw = strip_html(raw)
    digits = re.sub(r"[^\d+]", "", raw)
    if len(digits) < 6:
        return ""
    if any(digits.replace("+", "").startswith(prefix) for prefix in SITE_PHONE_PREFIXES):
        return ""
    return raw.strip()


def build_google_maps_url(parts: list[str]) -> str | None:
    cleaned = [strip_html(part) for part in parts if part and strip_html(part)]
    if not cleaned:
        return None
    query = ", ".join(cleaned)
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def decode_maps_url(url: str) -> str:
    return unescape(url.replace("&#038;", "&"))


class OsmedicaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch_json(self, url: str, params: dict | None = None) -> requests.Response:
        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response

    def fetch_all(self, endpoint: str, *, per_page: int = 100) -> dict[str, Any]:
        url = urljoin(BASE, endpoint)
        first = self.fetch_json(url, {"per_page": per_page, "page": 1})
        total_pages = int(first.headers.get("X-WP-TotalPages", "1") or 1)
        total = int(first.headers.get("X-WP-Total", "0") or 0)
        items = first.json()
        for page in range(2, total_pages + 1):
            response = self.fetch_json(url, {"per_page": per_page, "page": page})
            items.extend(response.json())
            time.sleep(0.08)
        return {
            "endpoint": endpoint,
            "total": total,
            "pages": total_pages,
            "items": items,
            "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def parse_listing_cards(html: str) -> dict[str, dict[str, Any]]:
    """Extrae fichas visibles en /cartilla/ (primer página del listado FacetWP)."""
    cards: dict[str, dict[str, Any]] = {}
    heading_pattern = re.compile(
        r'<h3[^>]*class="[^"]*elementor-heading-title[^"]*"[^>]*>(.*?)</h3>(.*?)(?=<h3[^>]*class="[^"]*elementor-heading-title|$)',
        re.IGNORECASE | re.DOTALL,
    )
    skip_titles = ("filtrar por", "enlaces útiles", "sedes administrativas", "querés sumarte")

    for match in heading_pattern.finditer(html):
        title = strip_html(match.group(1))
        if not title or any(title.casefold().startswith(prefix) for prefix in skip_titles):
            continue

        body = match.group(2)
        direccion_match = re.search(
            r"e-fas-home[\s\S]*?elementor-icon-list-text\">([^<]+)",
            body,
            re.IGNORECASE,
        )
        ubicacion_match = re.search(
            r"custom-term-list[\s\S]*?</svg>\s*([^<]+?)\s*</span>",
            body,
            re.IGNORECASE,
        )
        maps_matches = re.findall(
            r'href="(https://www\.google\.com/maps[^"]+)"',
            body,
            re.IGNORECASE,
        )
        telefonos: list[str] = []
        for raw in re.findall(
            r"elementor-icon-box-title\">\s*<span[^>]*>\s*([^<]+)",
            body,
            re.IGNORECASE,
        ):
            phone = clean_phone(raw)
            if phone and phone not in telefonos:
                telefonos.append(phone)
        for tel_href in re.findall(r'href="tel:([^"]+)"', body, re.IGNORECASE):
            phone = clean_phone(tel_href)
            if phone and phone not in telefonos:
                telefonos.append(phone)

        direccion = strip_html(direccion_match.group(1)) if direccion_match else None
        ubicacion = strip_html(ubicacion_match.group(1)) if ubicacion_match else None
        google_maps_url = decode_maps_url(maps_matches[0]) if maps_matches else None

        if not google_maps_url:
            query_parts = [part for part in (direccion, ubicacion) if part]
            google_maps_url = build_google_maps_url(query_parts)
            maps_origin = "generado" if google_maps_url else None
        else:
            maps_origin = "osmedica_listado"

        cards[normalize_title(title)] = {
            "direccion": direccion,
            "ubicacion": ubicacion,
            "telefonos": telefonos,
            "google_maps_url": google_maps_url,
            "google_maps_origen": maps_origin,
        }

    return cards


FACETWP_DEFAULT_FACETS: dict[str, Any] = {
    "prestador": [],
    "guardias": [],
    "especialidad": [],
    "estudios": [],
    "bsqueda": "",
    "zona_o_ubicacin": [],
    "zona": [],
}


def fetch_listing_cards_facetwp(session: requests.Session) -> dict[str, dict[str, Any]]:
    """Pagina el listado FacetWP vía POST JSON a /cartilla/ (54 páginas, ~10 fichas c/u)."""
    session.get(CARTILLA_URL, timeout=60)
    listing: dict[str, dict[str, Any]] = {}
    total_pages = 54

    for paged in range(1, total_pages + 1):
        body = {
            "action": "facetwp_refresh",
            "data": {
                "facets": dict(FACETWP_DEFAULT_FACETS),
                "frozen_facets": {},
                "http_params": {
                    "get": {"_paged": str(paged)} if paged > 1 else {},
                    "uri": "cartilla",
                    "url_vars": [],
                },
                "template": "wp",
                "extras": {"sort": "default"},
                "soft_refresh": 0 if paged > 1 else 1,
                "is_bfcache": 1,
                "first_load": 0,
                "paged": paged,
            },
        }
        response = session.post(
            CARTILLA_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        batch = parse_listing_cards(payload.get("template") or "")
        listing.update(batch)
        pager = (payload.get("settings") or {}).get("pager") or {}
        total_pages = int(pager.get("total_pages") or total_pages)
        print(
            f"Listado FacetWP p{paged}/{total_pages}: +{len(batch)} (total {len(listing)})",
            file=sys.stderr,
        )
        time.sleep(0.1)

    return listing


def build_taxonomy_maps(collections: dict[str, dict[str, Any]]) -> dict[str, dict[int, dict[str, Any]]]:
    maps: dict[str, dict[int, dict[str, Any]]] = {}
    for endpoint in TAXONOMY_ENDPOINTS:
        maps[endpoint] = {
            int(item["id"]): item for item in collections[endpoint]["items"]
        }
    return maps


def taxonomy_names(
    item: dict[str, Any],
    field: str,
    taxonomy_map: dict[int, dict[str, Any]],
) -> list[str]:
    names: list[str] = []
    for raw_id in item.get(field, []) or []:
        taxonomy_item = taxonomy_map.get(int(raw_id))
        if taxonomy_item and taxonomy_item.get("name"):
            names.append(unescape(str(taxonomy_item["name"])))
    return names


def taxonomy_refs(
    item: dict[str, Any],
    field: str,
    taxonomy_map: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for raw_id in item.get(field, []) or []:
        taxonomy_item = taxonomy_map.get(int(raw_id))
        if not taxonomy_item:
            continue
        refs.append(
            {
                "id": taxonomy_item.get("id"),
                "slug": taxonomy_item.get("slug"),
                "nombre": unescape(str(taxonomy_item.get("name", ""))),
            }
        )
    return refs


def contact_from_rest(
    *,
    nombre: str,
    zonas: list[dict[str, Any]],
    localidades: list[dict[str, Any]],
) -> dict[str, Any]:
    ubicacion_parts = []
    if localidades:
        ubicacion_parts.append(localidades[0]["nombre"])
    if zonas:
        ubicacion_parts.append(zonas[0]["nombre"])
    ubicacion = ", ".join(ubicacion_parts) if ubicacion_parts else None
    google_maps_url = build_google_maps_url([nombre, ubicacion] if ubicacion else [nombre])
    return {
        "direccion": None,
        "ubicacion": ubicacion,
        "telefonos": [],
        "google_maps_url": google_maps_url,
        "google_maps_origen": "generado" if google_maps_url else None,
    }


def merge_contact(
    *,
    nombre: str,
    zonas: list[dict[str, Any]],
    localidades: list[dict[str, Any]],
    listing: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    listing_contact = listing.get(normalize_title(nombre))
    if listing_contact:
        return dict(listing_contact)

    contact = contact_from_rest(nombre=nombre, zonas=zonas, localidades=localidades)
    if localidades or zonas:
        query_parts = []
        if contact.get("direccion"):
            query_parts.append(contact["direccion"])
        location_bits = [value["nombre"] for value in localidades + zonas]
        if location_bits:
            query_parts.append(", ".join(location_bits))
        contact["google_maps_url"] = build_google_maps_url(query_parts)
        contact["google_maps_origen"] = "generado" if contact["google_maps_url"] else None
    return contact


def normalize_cartilla_item(
    item: dict[str, Any],
    maps: dict[str, dict[int, dict[str, Any]]],
    listing: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    provincias = [
        maps["provincia"].get(int(pid))
        for pid in item.get("provincia", [])
        if maps["provincia"].get(int(pid))
    ]
    top_regions = [province for province in provincias if province and province.get("parent") == 0]
    sub_locations = [province for province in provincias if province and province.get("parent") != 0]

    zonas = [
        {
            "id": zone["id"],
            "slug": zone["slug"],
            "nombre": unescape(zone["name"]),
        }
        for zone in top_regions
    ]
    localidades = [
        {
            "id": location["id"],
            "slug": location["slug"],
            "nombre": unescape(location["name"]),
            "parent": location.get("parent"),
        }
        for location in sub_locations
    ]

    nombre = strip_html(item.get("title", {}).get("rendered", ""))
    contacto = merge_contact(
        nombre=nombre,
        zonas=zonas,
        localidades=localidades,
        listing=listing,
    )

    excerpt_rendered = item.get("excerpt", {}).get("rendered", "")
    excerpt = strip_html(excerpt_rendered) if excerpt_rendered else ""

    return {
        "id": item["id"],
        "slug": item["slug"],
        "nombre": nombre,
        "url": item.get("link"),
        "estado": item.get("status"),
        "tipo_prestador": taxonomy_names(item, "tipo_de_prestador", maps["tipo_de_prestador"]),
        "tipo_de_guardia": taxonomy_names(item, "tipo_de_guardia", maps["tipo_de_guardia"]),
        "especialidades": taxonomy_names(item, "especialidades", maps["especialidades"]),
        "estudios": taxonomy_names(item, "estudios", maps["estudios"]),
        "zonas": zonas,
        "localidades": localidades,
        "class_list": item.get("class_list", []),
        "fecha_publicacion": item.get("date"),
        "modified": item.get("modified"),
        "excerpt": excerpt,
        "contacto": contacto,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_sync() -> dict[str, Any]:
    client = OsmedicaClient()
    collections: dict[str, dict[str, Any]] = {}

    for endpoint in [*TAXONOMY_ENDPOINTS, CARTILLA_ENDPOINT]:
        print(f"Descargando {endpoint}...", file=sys.stderr)
        collections[endpoint] = client.fetch_all(endpoint)

    listing_cards = fetch_listing_cards_facetwp(client.session)
    print(
        f"Fichas con contacto del listado FacetWP: {len(listing_cards)}",
        file=sys.stderr,
    )

    taxonomy_maps = build_taxonomy_maps(collections)
    normalized = [
        normalize_cartilla_item(item, taxonomy_maps, listing_cards)
        for item in collections[CARTILLA_ENDPOINT]["items"]
    ]

    with_maps_listado = sum(
        1 for row in normalized if row["contacto"].get("google_maps_origen") == "osmedica_listado"
    )
    with_maps = sum(1 for row in normalized if row["contacto"].get("google_maps_url"))

    summary = {
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {key: value["total"] for key, value in collections.items()},
        "listing_cards_parsed": len(listing_cards),
        "prestadores_con_maps_listado": with_maps_listado,
        "prestadores_con_maps": with_maps,
        "tipo_prestador": [
            {
                "id": item["id"],
                "name": item["name"],
                "slug": item["slug"],
                "count": item.get("count", 0),
            }
            for item in collections["tipo_de_prestador"]["items"]
        ],
        "tipo_de_guardia": [
            {
                "id": item["id"],
                "name": item["name"],
                "slug": item["slug"],
                "count": item.get("count", 0),
            }
            for item in collections["tipo_de_guardia"]["items"]
        ],
        "top_level_zonas": [
            {
                "id": item["id"],
                "name": item["name"],
                "slug": item["slug"],
                "count": item.get("count", 0),
            }
            for item in collections["provincia"]["items"]
            if item.get("parent") == 0
        ],
        "sample_cartilla": normalized[:10],
    }

    # Archivos usados por la API
    write_json(RESEARCH_DIR / "cartilla.normalized.json", normalized)
    write_json(RESEARCH_DIR / "summary.json", summary)
    write_json(RESEARCH_DIR / "tipo_de_prestador.json", collections["tipo_de_prestador"])
    write_json(RESEARCH_DIR / "tipo_de_guardia.json", collections["tipo_de_guardia"])
    write_json(RESEARCH_DIR / "provincia.json", collections["provincia"])
    write_json(RESEARCH_DIR / "especialidades.json", collections["especialidades"])
    write_json(RESEARCH_DIR / "estudios.json", collections["estudios"])
    write_json(RESEARCH_DIR / "cartilla.json", collections["cartilla"])

    # Copia cruda archivada (opcional, histórico)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for endpoint, payload in collections.items():
        write_json(ARCHIVE_DIR / f"{endpoint}.json", payload)
    write_json(ARCHIVE_DIR / "cartilla.normalized.json", normalized)
    write_json(ARCHIVE_DIR / "listing_cards.json", listing_cards)

    return summary


def main() -> int:
    try:
        summary = run_sync()
    except requests.RequestException as exc:
        print(f"Error de red al sincronizar: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
