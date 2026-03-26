# Análisis de estructura de datos - OSMEDICA Cartilla

## 1. Fuente principal detectada

La cartilla pública usa WordPress REST API como backend de contenido. No conviene empezar por scraping del HTML visual, porque ya existe una capa estructurada reutilizable.

### Endpoints públicos confirmados

- `https://osmedica.com.ar/wp-json/wp/v2/cartilla`
- `https://osmedica.com.ar/wp-json/wp/v2/tipo_de_prestador`
- `https://osmedica.com.ar/wp-json/wp/v2/provincia`
- `https://osmedica.com.ar/wp-json/wp/v2/especialidades`
- `https://osmedica.com.ar/wp-json/wp/v2/estudios`

## 2. Volumen del dataset

Conteos relevados:

- `cartilla`: **538** fichas
- `tipo_de_prestador`: **11**
- `provincia`: **126**
- `especialidades`: **151**
- `estudios`: **234**

## 3. Modelo actual de WordPress

### Post type `cartilla`
Campos detectados vía `OPTIONS /wp-json/wp/v2/cartilla`:

- `id`
- `date`
- `date_gmt`
- `guid`
- `link`
- `modified`
- `modified_gmt`
- `slug`
- `status`
- `type`
- `password`
- `permalink_template`
- `generated_slug`
- `class_list`
- `title`
- `excerpt`
- `template`
- `especialidades`
- `estudios`
- `provincia`
- `tipo_de_prestador`

### Taxonomías

Cada ficha puede relacionarse con:

- uno o varios `tipo_de_prestador`
- cero o varias `especialidades`
- cero o varios `estudios`
- una o varias entradas de `provincia`

## 4. Hallazgo importante: `provincia` en realidad modela geografía jerárquica

Aunque la taxonomía se llama `provincia`, en la práctica mezcla:

- regiones macro: `Capital Federal`, `GBA Zona Sur`, `GBA Zona Norte`, `GBA Zona Oeste`, `Buenos Aires`, `Villa de Mayo`
- localidades / barrios hijos: `Quilmes`, `Avellaneda`, `Palermo`, `Recoleta`, etc.

### Zonas raíz detectadas

- Buenos Aires
- Capital Federal
- GBA Zona Norte
- GBA Zona Oeste
- GBA Zona Sur
- Villa de Mayo

Esto implica que para la API propia conviene renombrar conceptualmente:

- `provincia.parent == 0` → `region`
- `provincia.parent != 0` → `localidad`

## 5. Cobertura de campos por ficha

Sobre 538 fichas normalizadas:

- con `tipo_prestador`: **534**
- con `especialidades`: **196**
- con `estudios`: **118**
- con `zonas`: **533**
- con `localidades`: **525**
- con `especialidades` y `estudios`: **72**
- sin localidad: **13**
- sin zona: **5**

## 6. Tipos de prestador

Conteos observados:

- Centros de Diálisis: 46
- Centros, Clínicas y Sanatorios: 139
- Estudios o prácticas: 110
- Farmacias: 139
- Guardia Médica: 46
- Guardia Odontológica: 6
- Guardia Psiquiátrica: 3
- Odontología: 58
- Ópticas: 108
- Profesionales: 50
- Urgencias: 2

### Observación

No son mutuamente excluyentes. Hay **135 fichas** con más de un tipo de prestador.

Ejemplos:

- Centro Médico Liniers → Centros, Estudios, Odontología
- Policlínico Regional Avellaneda → Centros, Estudios, Guardia Médica
- Clínica COMAVE → Centros + Guardia Psiquiátrica

Esto sugiere que en la API propia no debería existir un solo campo `tipo`, sino una colección `categorias` o `tiposPrestador`.

## 7. Especialidades más frecuentes

Top relevado:

- Ginecología (63)
- Cardiología (62)
- Clínica médica (61)
- Odontología General (49)
- Dermatología (48)
- Nutrición (46)
- Pediatría (46)
- Gastroenterología (45)
- Urología (44)
- Cirugía general (44)
- Neurología (41)
- Otorrinolaringología (38)

## 8. Localidades / barrios más frecuentes

Top relevado:

- Palermo (23)
- Recoleta (21)
- Lanús (20)
- San Martín (14)
- Belgrano (14)
- Caballito (14)
- Quilmes (13)
- San Miguel (13)
- San Nicolás (13)
- Balvanera (13)

## 9. Frontend actual: reglas FacetWP detectadas

La web no solo filtra; además oculta ciertos selectores según el tipo de prestador.

Reglas detectadas:

- si `prestador = especialidad` → ocultar filtro de estudios
- si `prestador = estudio` → ocultar filtro de especialidades
- si `prestador = urgencias` → ocultar especialidades y estudios
- si `prestador = optica` → ocultar especialidades y estudios
- si `prestador = farmacia` → ocultar especialidades y estudios

### Implicancia

La API propia puede ser más inteligente que el sitio actual:

- exponer metadatos de filtros disponibles por tipo
- devolver `availableFilters` según la categoría elegida
- evitar UX confusa en frontend

## 10. Limitaciones de la REST API pública actual

La REST API pública expone bien taxonomías y relaciones, pero **no parece exponer atributos ricos de detalle** como:

- dirección postal
- teléfono específico por ficha
- horarios
- observaciones
- cobertura
- coordenadas

## 11. Prueba de páginas de detalle

Se probó una muestra de 30 páginas de detalle.

Resultados:

- todas devolvieron links `tel:` en el HTML completo del sitio
- pero el contenido dentro de `<main>` está casi vacío
- los teléfonos detectados parecen venir del layout/footer global, no necesariamente de la ficha
- no se detectaron `mailto`, enlaces directos a Google Maps ni WhatsApp en la muestra

### Conclusión provisional

Las páginas públicas de detalle **no parecen contener el detalle clínico enriquecido de forma visible en HTML estándar**, al menos no de manera trivialmente scrapeable.

Eso abre tres posibilidades:

1. el sitio realmente no publica esos campos
2. los campos existen en el admin pero no están expuestos por REST
3. los datos están cargados por algún mecanismo/plugin no visible en el HTML simple

## 12. Recomendación técnica para la API propia

### Fase 1
Armar API propia apoyada en la REST pública existente:

- normalización de taxonomías
- indexación de texto
- filtros consistentes
- endpoints de búsqueda
- agregados/facetas

### Fase 2
Auditar si OSMEDICA tiene datos más ricos en otro origen:

- endpoints alternativos
- exportaciones internas
- CSV/Excel
- acceso al WordPress de origen

### Fase 3
Si aparecen más campos, enriquecer el índice propio.

## 13. Modelo conceptual sugerido para la API propia

```json
{
  "id": 6546,
  "nombre": "Dra. Leslie Rosmarino",
  "slug": "dra-leslie-rosmarino",
  "tiposPrestador": ["Odontología"],
  "especialidades": ["Odontología General"],
  "estudios": [],
  "ubicaciones": [
    {
      "region": "GBA Zona Sur",
      "localidad": "Quilmes"
    }
  ],
  "source": {
    "provider": "wordpress",
    "url": "https://osmedica.com.ar/cartilla/dra-leslie-rosmarino/",
    "lastModified": "2026-03-20T08:56:20"
  }
}
```

## 14. Decisión práctica actual

Con lo relevado hasta ahora:

- **sí hay base suficiente para empezar una API propia ya**
- **no hay evidencia todavía de un detalle clínico enriquecido públicamente accesible**
- por eso la primera versión debería enfocarse en:
  - búsqueda
  - filtros
  - taxonomías limpias
  - relevancia
  - UX de consulta

En otras palabras: ya se puede construir un producto mejor que la cartilla actual, incluso sin datos extra.
