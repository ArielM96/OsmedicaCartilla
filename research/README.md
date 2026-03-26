# OSMEDICA Cartilla - relevamiento técnico

Objetivo: mapear la estructura de datos expuesta por la cartilla pública de OSMEDICA para usarla como base de una API propia bajo dominio propio.

## Hipótesis inicial

La cartilla pública no necesita scraping visual como primer paso, porque expone datos estructurados vía WordPress REST API.

## Hallazgos iniciales

Endpoints detectados:

- `/wp-json/wp/v2/cartilla`
- `/wp-json/wp/v2/tipo_de_prestador`
- `/wp-json/wp/v2/provincia`
- `/wp-json/wp/v2/especialidades`
- `/wp-json/wp/v2/estudios`

También se detectó que la UI usa FacetWP en frontend, pero para nuestra API conviene tomar como fuente principal la REST API de WordPress, no la capa de rendering del sitio.

## Enfoque de trabajo

1. Descubrir todos los endpoints públicos relevantes.
2. Descargar datasets completos paginados.
3. Construir mapas de taxonomías:
   - tipo de prestador
   - provincia / zona / localidad
   - especialidades
   - estudios
4. Normalizar el contenido de `cartilla` en una estructura propia.
5. Probar si las páginas de detalle contienen datos adicionales no expuestos en la REST API.
6. Documentar gaps para decidir si alcanza con WP JSON o si hace falta scraping/enriquecimiento híbrido.

## Archivos generados

- `discover.py`: script de relevamiento
- `tipo_de_prestador.json`
- `provincia.json`
- `especialidades.json`
- `estudios.json`
- `cartilla.json`
- `cartilla.normalized.json`
- `summary.json`
- `detail-page-probe.json`

## Próximo objetivo

Terminar el relevamiento y responder:

- cuántos prestadores hay
- qué taxonomías existen realmente
- cómo está modelada la geografía
- qué campos faltan para una API de buena UX
- si conviene sync puro o sync + scraping de detalle
