from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    id: Optional[int] = None
    slug: str
    nombre: str
    count: int = 0
    parent: Optional[int] = None


class CatalogRef(BaseModel):
    id: Optional[int] = None
    slug: str
    nombre: str


class SourceInfo(BaseModel):
    provider: str = "wordpress"
    url: str
    lastModified: Optional[str] = None


class ContactoInfo(BaseModel):
    direccion: Optional[str] = None
    ubicacion: Optional[str] = None
    telefonos: List[str] = Field(default_factory=list)
    googleMapsUrl: Optional[str] = None
    googleMapsOrigen: Optional[str] = None


class LocationItem(BaseModel):
    id: Optional[int] = None
    slug: str
    nombre: str
    parent: Optional[int] = None


class PrestadorItem(BaseModel):
    id: int
    slug: str
    nombre: str
    tiposPrestador: List[CatalogRef] = Field(default_factory=list)
    tiposGuardia: List[CatalogRef] = Field(default_factory=list)
    especialidades: List[CatalogRef] = Field(default_factory=list)
    estudios: List[CatalogRef] = Field(default_factory=list)
    regiones: List[LocationItem] = Field(default_factory=list)
    localidades: List[LocationItem] = Field(default_factory=list)
    contacto: ContactoInfo = Field(default_factory=ContactoInfo)
    source: SourceInfo


class FacetValue(BaseModel):
    slug: str
    nombre: str
    count: int


class Pagination(BaseModel):
    page: int
    limit: int
    totalItems: int
    totalPages: int


class PrestadorListResponse(BaseModel):
    items: List[PrestadorItem]
    pagination: Pagination
    facets: Optional[dict[str, List[FacetValue]]] = None


class SuggestionItem(BaseModel):
    type: str
    slug: str
    nombre: str


class SuggestionsResponse(BaseModel):
    suggestions: List[SuggestionItem]
