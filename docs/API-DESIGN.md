# API Design - OSMEDICA Cartilla API

## 1. Principios

- respuestas limpias y consistentes
- nombres de campos orientados al producto, no al CMS original
- filtros combinables
- soporte para facetas
- paginación estándar
- trazabilidad del origen

## 2. Modelo conceptual

## Prestador

```json
{
  "id": 6546,
  "slug": "dra-leslie-rosmarino",
  "nombre": "Dra. Leslie Rosmarino",
  "tiposPrestador": [
    { "id": 564, "slug": "odontologia", "nombre": "Odontología" }
  ],
  "especialidades": [
    { "id": 40, "slug": "odontologia-general", "nombre": "Odontología General" }
  ],
  "estudios": [],
  "ubicaciones": [
    {
      "region": { "id": 84, "slug": "gba-zona-sur", "nombre": "GBA Zona Sur" },
      "localidad": { "id": 85, "slug": "quilmes", "nombre": "Quilmes" }
    }
  ],
  "source": {
    "provider": "wordpress",
    "url": "https://osmedica.com.ar/cartilla/dra-leslie-rosmarino/",
    "lastModified": "2026-03-20T08:56:20"
  }
}
```

## 3. Endpoints propuestos

### GET /api/v1/prestadores

Lista paginada con filtros.

#### Query params

- `q`
- `tipoPrestador`
- `especialidad`
- `estudio`
- `region`
- `localidad`
- `page`
- `limit`
- `sort`
- `includeFacets`

#### Ejemplo

`/api/v1/prestadores?q=cardiologia&region=gba-zona-sur&localidad=quilmes&limit=20`

#### Response

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 120,
    "totalPages": 6
  },
  "facets": {
    "tiposPrestador": [],
    "especialidades": [],
    "estudios": [],
    "regiones": [],
    "localidades": []
  }
}
```

### GET /api/v1/prestadores/:id

Devuelve el detalle normalizado de un prestador.

### GET /api/v1/prestadores/:slug

Opcional si se prefiere lookup por slug.

### GET /api/v1/catalogos/tipos-prestador

### GET /api/v1/catalogos/especialidades

### GET /api/v1/catalogos/estudios

### GET /api/v1/catalogos/regiones

### GET /api/v1/catalogos/localidades

Puede aceptar `region=` para traer solo localidades de una región.

### GET /api/v1/busqueda/sugerencias

Autocompletado de términos.

#### Query params

- `q`
- `limit`

#### Response ejemplo

```json
{
  "suggestions": [
    { "type": "especialidad", "slug": "cardiologia", "nombre": "Cardiología" },
    { "type": "localidad", "slug": "quilmes", "nombre": "Quilmes" }
  ]
}
```

### GET /api/v1/health

Chequeo simple del servicio.

### POST /api/v1/admin/sync

Trigger manual de sincronización.

Inicialmente puede quedar protegido o incluso fuera del API público.

## 4. Facetas sugeridas

La respuesta de `/prestadores` puede devolver conteos así:

```json
{
  "facets": {
    "tiposPrestador": [
      { "slug": "farmacia", "nombre": "Farmacias", "count": 21 }
    ],
    "especialidades": [
      { "slug": "cardiologia", "nombre": "Cardiología", "count": 11 }
    ],
    "regiones": [
      { "slug": "gba-zona-sur", "nombre": "GBA Zona Sur", "count": 34 }
    ],
    "localidades": [
      { "slug": "quilmes", "nombre": "Quilmes", "count": 8 }
    ]
  }
}
```

## 5. Reglas de normalización

### Geografía

Taxonomía `provincia` del origen se mapea a:

- `region` si `parent == 0`
- `localidad` si `parent != 0`

### Tipos de prestador

Mantener pluralidad. Nunca asumir unicidad.

### Especialidades y estudios

Permitir coexistencia en una misma ficha.

### Nombre

Usar `title.rendered` limpiando entidades HTML.

## 6. Estrategia de búsqueda

### MVP

- búsqueda simple sobre `nombre`
- búsqueda sobre especialidades
- búsqueda sobre estudios
- búsqueda sobre localidad/región
- ranking básico por coincidencia exacta + prefijo + contains

### Evolución

- sinónimos: "otorrino" -> "otorrinolaringología"
- corrección leve de tildes
- expansión de términos comunes
- ranking por tipo de entidad

## 7. Versionado

Usar prefijo:

- `/api/v1/...`

## 8. Errores

Formato sugerido:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "El parámetro 'limit' debe estar entre 1 y 100"
  }
}
```

## 9. Contrato de sync interno

Pipeline recomendado:

1. fetch taxonomías
2. fetch cartilla paginada
3. resolver relaciones
4. normalizar
5. persistir en DB propia
6. recalcular índices/facetas

## 10. Campos a prever para futuro

Aunque hoy no estén disponibles, conviene dejar espacio para:

- `direccion`
- `telefonos`
- `horarios`
- `coordenadas`
- `observaciones`
- `cobertura`
- `guardia`
