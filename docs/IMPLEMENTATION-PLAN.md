# Implementation Plan - OSMEDICA Cartilla API

## 1. Stack recomendado

### Backend

Opción recomendada:

- **FastAPI + PostgreSQL**

Alternativa:

- **NestJS + PostgreSQL**

### Búsqueda

#### MVP
- PostgreSQL full-text + índices trigram

#### Evolución
- Meilisearch o Elasticsearch

### Infra

- API bajo subdominio propio, por ejemplo: `api.tudominio.com`
- cron o scheduler para sync
- reverse proxy (Nginx / Caddy)
- observabilidad básica

## 2. Arquitectura propuesta

### Componentes

1. **Ingestor**
   - consume WordPress REST API
   - descarga taxonomías y fichas

2. **Normalizer**
   - transforma el modelo origen al modelo propio
   - resuelve región/localidad
   - limpia nombres y relaciones

3. **Storage**
   - guarda entidades normalizadas en PostgreSQL

4. **Indexer**
   - construye campos de búsqueda y facetas

5. **Public API**
   - expone consultas REST

## 3. Modelo de base de datos sugerido

### tablas

#### providers
- id
- source_id
- slug
- name
- source_url
- source_last_modified
- raw_payload jsonb
- normalized_payload jsonb
- created_at
- updated_at

#### provider_types
- id
- source_id
- slug
- name

#### specialties
- id
- source_id
- slug
- name

#### studies
- id
- source_id
- slug
- name

#### regions
- id
- source_id
- slug
- name

#### localities
- id
- source_id
- region_id
- slug
- name

#### provider_provider_types
- provider_id
- provider_type_id

#### provider_specialties
- provider_id
- specialty_id

#### provider_studies
- provider_id
- study_id

#### provider_locations
- provider_id
- region_id
- locality_id

#### sync_runs
- id
- started_at
- finished_at
- status
- stats jsonb
- error_message

## 4. Fases de implementación

### Fase 0 - documentación y setup
- definir stack final
- crear repo limpio
- dejar docs base

### Fase 1 - ingesta
- portar `discover.py` a módulo del proyecto
- implementar cliente WordPress
- descargar taxonomías paginadas
- descargar cartilla paginada
- persistir raw payloads

### Fase 2 - normalización
- mapear `provincia` a región/localidad
- normalizar nombres
- armar relaciones n:n
- detectar inconsistencias

### Fase 3 - API pública MVP
- `GET /prestadores`
- `GET /prestadores/:id`
- `GET /catalogos/*`
- búsqueda básica
- paginación
- facetas

### Fase 4 - calidad de búsqueda
- ranking mejorado
- soporte sin tildes
- prefijos y trigram
- sugerencias

### Fase 5 - operaciones
- endpoint o job de sync
- logs
- métricas
- caché

## 5. Orden de desarrollo recomendado en Cursor

1. scaffolding backend
2. models + migrations
3. cliente ingestión WP
4. normalizador
5. comando `sync`
6. endpoints catálogo
7. endpoints prestadores
8. búsqueda/facetas
9. tests
10. deploy

## 6. Contratos internos sugeridos

### servicio de sync

- `run_full_sync()`
- `fetch_taxonomies()`
- `fetch_cartilla()`
- `normalize_provider()`
- `upsert_provider()`

### servicio de búsqueda

- `search_providers(filters)`
- `build_facets(filters)`
- `get_provider_detail(id)`
- `suggest(query)`

## 7. MVP técnico concreto

### Entregables del MVP

- base PostgreSQL
- script o comando de sync
- API REST pública v1
- documentación OpenAPI
- despliegue en subdominio propio

### MVP funcional mínimo

- listar prestadores
- buscar por texto
- filtrar por:
  - tipo de prestador
  - especialidad
  - estudio
  - región
  - localidad
- devolver total y facetas

## 8. Riesgos técnicos y mitigación

### Riesgo: cambios en WP API
Mitigación:
- desacoplar fetchers
- guardar raw payloads
- tests de contrato simples

### Riesgo: datos incompletos
Mitigación:
- diseñar modelo extensible
- no bloquear MVP por campos faltantes

### Riesgo: búsqueda pobre
Mitigación:
- empezar con Postgres trigram + unaccent
- evolucionar si hace falta

## 9. Deploy sugerido

### Simple
- VPS
- Docker Compose
- API + Postgres + reverse proxy

### Variables base
- `DATABASE_URL`
- `SOURCE_WP_BASE_URL`
- `SYNC_ENABLED`
- `SYNC_SCHEDULE`
- `API_BASE_URL`

## 10. Próximos documentos útiles

- `ARCHITECTURE.md`
- `DATA-MODEL.md`
- `OPENAPI.yaml`
- `DECISIONS.md`
- `BACKLOG.md`
