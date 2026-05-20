from __future__ import annotations

import json
import math
import unicodedata
from collections import Counter
from functools import lru_cache
from html import unescape
from pathlib import Path
from typing import Any

from .config import (
    DATASET_PATH,
    ESPECIALIDADES_PATH,
    ESTUDIOS_PATH,
    TIPOS_GUARDIA_PATH,
    TIPOS_PRESTADOR_PATH,
)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold().strip()


def _item_id(index: dict[str, dict[str, Any]], slug: str) -> int | None:
    item = index.get(slug)
    if not item:
        return None
    return item.get("id")


class CartillaStore:
    def __init__(self, dataset_path: Path) -> None:
        self.taxonomy_index = self._load_taxonomy_index()
        raw_entries = json.loads(dataset_path.read_text())
        self.entries: list[dict[str, Any]] = [self._normalize_entry(item) for item in raw_entries]
        self.by_id = {entry["id"]: entry for entry in self.entries}
        self.by_slug = {entry["slug"]: entry for entry in self.entries}
        self.catalogs = self._build_catalogs()
        self.localidades_by_region = self._build_localidades_by_region()
        self.suggestions = self._build_suggestions()

    def _normalize_entry(self, item: dict[str, Any]) -> dict[str, Any]:
        regiones = [
            {
                "id": zone.get("id"),
                "slug": zone.get("slug"),
                "nombre": unescape(zone.get("nombre", "")),
            }
            for zone in item.get("zonas", [])
        ]
        localidades = [
            {
                "id": location.get("id"),
                "slug": location.get("slug"),
                "nombre": unescape(location.get("nombre", "")),
                "parent": location.get("parent"),
            }
            for location in item.get("localidades", [])
        ]

        tipos_prestador = [
            self._taxonomy_item("tiposPrestador", name)
            for name in item.get("tipo_prestador", [])
        ]
        tipos_guardia = [
            self._taxonomy_item("tiposGuardia", name)
            for name in item.get("tipo_de_guardia", [])
        ]
        especialidades = [
            self._taxonomy_item("especialidades", name)
            for name in item.get("especialidades", [])
        ]
        estudios = [
            self._taxonomy_item("estudios", name)
            for name in item.get("estudios", [])
        ]
        contacto_raw = item.get("contacto") or {}
        contacto = {
            "direccion": contacto_raw.get("direccion"),
            "ubicacion": contacto_raw.get("ubicacion"),
            "telefonos": list(contacto_raw.get("telefonos") or []),
            "googleMapsUrl": contacto_raw.get("google_maps_url"),
            "googleMapsOrigen": contacto_raw.get("google_maps_origen"),
        }

        search_parts = [
            item.get("nombre", ""),
            contacto.get("direccion") or "",
            contacto.get("ubicacion") or "",
            *[value["nombre"] for value in tipos_prestador],
            *[value["nombre"] for value in tipos_guardia],
            *[value["nombre"] for value in especialidades],
            *[value["nombre"] for value in estudios],
            *[value["nombre"] for value in regiones],
            *[value["nombre"] for value in localidades],
        ]

        return {
            "id": item["id"],
            "slug": item["slug"],
            "nombre": unescape(item["nombre"]),
            "tiposPrestador": tipos_prestador,
            "tiposGuardia": tipos_guardia,
            "especialidades": especialidades,
            "estudios": estudios,
            "regiones": regiones,
            "localidades": localidades,
            "contacto": contacto,
            "source": {
                "provider": "wordpress",
                "url": item.get("url"),
                "lastModified": item.get("modified"),
            },
            "search_text": " ".join(_normalize_text(part) for part in search_parts if part),
        }

    def _slugify(self, value: str) -> str:
        return _normalize_text(value).replace(" ", "-")

    def _load_taxonomy_index(self) -> dict[str, dict[str, dict[str, Any]]]:
        sources = {
            "tiposPrestador": TIPOS_PRESTADOR_PATH,
            "tiposGuardia": TIPOS_GUARDIA_PATH,
            "especialidades": ESPECIALIDADES_PATH,
            "estudios": ESTUDIOS_PATH,
        }
        indexes: dict[str, dict[str, dict[str, Any]]] = {}
        for key, path in sources.items():
            if not path.exists():
                indexes[key] = {}
                continue
            payload = json.loads(path.read_text())
            items = payload.get("items", [])
            indexes[key] = {
                _normalize_text(unescape(item["name"])): {
                    "id": item["id"],
                    "slug": item["slug"],
                    "nombre": unescape(item["name"]),
                }
                for item in items
            }
        return indexes

    def _taxonomy_item(self, taxonomy: str, raw_name: str) -> dict[str, Any]:
        clean_name = unescape(raw_name)
        matched = self.taxonomy_index.get(taxonomy, {}).get(_normalize_text(clean_name))
        if matched:
            return dict(matched)
        return {
            "id": None,
            "slug": self._slugify(clean_name),
            "nombre": clean_name,
        }

    def _build_catalogs(self) -> dict[str, list[dict[str, Any]]]:
        tipo_counts: Counter[str] = Counter()
        tipo_items: dict[str, dict[str, Any]] = {}
        guardia_counts: Counter[str] = Counter()
        guardia_items: dict[str, dict[str, Any]] = {}
        especialidad_counts: Counter[str] = Counter()
        especialidad_items: dict[str, dict[str, Any]] = {}
        estudio_counts: Counter[str] = Counter()
        estudio_items: dict[str, dict[str, Any]] = {}
        region_counts: Counter[str] = Counter()
        region_items: dict[str, dict[str, Any]] = {}
        localidad_counts: Counter[str] = Counter()
        localidad_items: dict[str, dict[str, Any]] = {}

        for entry in self.entries:
            for item in entry["tiposPrestador"]:
                tipo_counts[item["slug"]] += 1
                tipo_items[item["slug"]] = item
            for item in entry["tiposGuardia"]:
                guardia_counts[item["slug"]] += 1
                guardia_items[item["slug"]] = item
            for item in entry["especialidades"]:
                especialidad_counts[item["slug"]] += 1
                especialidad_items[item["slug"]] = item
            for item in entry["estudios"]:
                estudio_counts[item["slug"]] += 1
                estudio_items[item["slug"]] = item
            for item in entry["regiones"]:
                region_counts[item["slug"]] += 1
                region_items[item["slug"]] = item
            for item in entry["localidades"]:
                localidad_counts[item["slug"]] += 1
                localidad_items[item["slug"]] = item

        def build_from_counts(
            counts: Counter[str],
            names: dict[str, str] | None = None,
            items: dict[str, dict[str, Any]] | None = None,
        ) -> list[dict[str, Any]]:
            built = []
            for slug, count in counts.items():
                if items:
                    value = dict(items[slug])
                    value["count"] = count
                    built.append(value)
                else:
                    built.append({"slug": slug, "nombre": names[slug], "count": count})
            return sorted(built, key=lambda item: (item["nombre"].casefold(), item["slug"]))

        return {
            "tiposPrestador": build_from_counts(tipo_counts, items=tipo_items),
            "tiposGuardia": build_from_counts(guardia_counts, items=guardia_items),
            "especialidades": build_from_counts(especialidad_counts, items=especialidad_items),
            "estudios": build_from_counts(estudio_counts, items=estudio_items),
            "regiones": build_from_counts(region_counts, items=region_items),
            "localidades": build_from_counts(localidad_counts, items=localidad_items),
        }

    def _build_localidades_by_region(self) -> dict[str, list[dict[str, Any]]]:
        region_slug_by_id = {item["id"]: item["slug"] for item in self.catalogs["regiones"] if item.get("id") is not None}
        mapping: dict[str, list[dict[str, Any]]] = {}
        for item in self.catalogs["localidades"]:
            parent_id = item.get("parent")
            region_slug = region_slug_by_id.get(parent_id)
            if not region_slug:
                continue
            mapping.setdefault(region_slug, []).append(item)

        for region_slug in mapping:
            mapping[region_slug].sort(key=lambda item: (item["nombre"].casefold(), item["slug"]))
        return mapping

    def _build_suggestions(self) -> list[dict[str, str]]:
        suggestions: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def add_items(kind: str, items: list[dict[str, Any]]) -> None:
            for item in items:
                key = (kind, item["slug"])
                if key in seen:
                    continue
                seen.add(key)
                suggestions.append({"type": kind, "slug": item["slug"], "nombre": item["nombre"]})

        add_items("prestador", [{"slug": entry["slug"], "nombre": entry["nombre"]} for entry in self.entries])
        add_items("tipoPrestador", self.catalogs["tiposPrestador"])
        add_items("tipoGuardia", self.catalogs["tiposGuardia"])
        add_items("especialidad", self.catalogs["especialidades"])
        add_items("estudio", self.catalogs["estudios"])
        add_items("region", self.catalogs["regiones"])
        add_items("localidad", self.catalogs["localidades"])

        suggestions.sort(key=lambda item: (item["nombre"].casefold(), item["slug"]))
        return suggestions

    def list_prestadores(
        self,
        *,
        q: str | None,
        tipo_prestador: str | None,
        especialidad: str | None,
        estudio: str | None,
        region: str | None,
        localidad: str | None,
        page: int,
        limit: int,
        include_facets: bool,
    ) -> dict[str, Any]:
        results = []
        normalized_query = _normalize_text(q) if q else None

        for entry in self.entries:
            if normalized_query and normalized_query not in entry["search_text"]:
                continue
            if tipo_prestador and not self._matches_slug(entry["tiposPrestador"], tipo_prestador):
                continue
            if especialidad and not self._matches_slug(entry["especialidades"], especialidad):
                continue
            if estudio and not self._matches_slug(entry["estudios"], estudio):
                continue
            if region and not self._matches_slug(entry["regiones"], region):
                continue
            if localidad and not self._matches_slug(entry["localidades"], localidad):
                continue
            results.append(entry)

        results.sort(key=lambda item: (item["nombre"].casefold(), item["id"]))

        total_items = len(results)
        total_pages = max(1, math.ceil(total_items / limit)) if limit else 1
        start = (page - 1) * limit
        end = start + limit

        payload: dict[str, Any] = {
            "items": results[start:end],
            "pagination": {
                "page": page,
                "limit": limit,
                "totalItems": total_items,
                "totalPages": total_pages,
            },
        }
        if include_facets:
            payload["facets"] = self._build_facets(results)
        return payload

    def get_prestador(self, identifier: str) -> dict[str, Any] | None:
        if identifier.isdigit():
            return self.by_id.get(int(identifier))
        return self.by_slug.get(identifier)

    def list_catalog(self, name: str, *, region: str | None = None) -> list[dict[str, Any]]:
        if name == "localidades" and region:
            return self.localidades_by_region.get(region, [])
        return self.catalogs[name]

    def suggestions_for(self, query: str, limit: int) -> list[dict[str, str]]:
        normalized_query = _normalize_text(query)
        if not normalized_query:
            return []
        matches = [
            item for item in self.suggestions if normalized_query in _normalize_text(item["nombre"]) or normalized_query in item["slug"]
        ]
        matches.sort(
            key=lambda item: (
                not _normalize_text(item["nombre"]).startswith(normalized_query),
                len(item["nombre"]),
                item["nombre"].casefold(),
            )
        )
        return matches[:limit]

    def _matches_slug(self, items: list[dict[str, Any]], expected_slug: str) -> bool:
        return any(item["slug"] == expected_slug for item in items)

    def _build_facets(self, entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        facets = {}
        for facet_name in ("tiposPrestador", "especialidades", "estudios", "regiones", "localidades"):
            counts: Counter[tuple[str, str]] = Counter()
            for entry in entries:
                seen = {(item["slug"], item["nombre"]) for item in entry[facet_name]}
                for key in seen:
                    counts[key] += 1
            facets[facet_name] = [
                {"slug": slug, "nombre": nombre, "count": count}
                for (slug, nombre), count in sorted(counts.items(), key=lambda item: (-item[1], item[0][1].casefold()))
            ]
        return facets


@lru_cache
def get_store() -> CartillaStore:
    return CartillaStore(DATASET_PATH)
