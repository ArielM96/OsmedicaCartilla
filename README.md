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
- diseño de API en preparación

## Estructura

- `docs/` → PRD, arquitectura, contratos y decisiones
- `research/` → datasets y análisis inicial
- `backend/` → implementación futura de la API
- `frontend/` → cliente o demo futura

## Fuente pública detectada

- `https://osmedica.com.ar/wp-json/wp/v2/cartilla`
- `https://osmedica.com.ar/wp-json/wp/v2/tipo_de_prestador`
- `https://osmedica.com.ar/wp-json/wp/v2/provincia`
- `https://osmedica.com.ar/wp-json/wp/v2/especialidades`
- `https://osmedica.com.ar/wp-json/wp/v2/estudios`
