# PRD - OSMEDICA Cartilla API

## 1. Resumen

Construir una API propia para la cartilla de OSMEDICA usando como base la fuente pública actual, pero mejorando drásticamente la experiencia de búsqueda, filtros, consistencia de datos y capacidad de integración con productos web, mobile y asistentes.

## 2. Problema

La cartilla actual presenta limitaciones típicas de un sitio WordPress orientado a frontend:

- taxonomías difíciles de reutilizar desde otros productos
- filtros poco expresivos o acoplados a la UI original
- búsquedas limitadas
- geografía modelada de forma confusa
- dificultad para integrar con aplicaciones propias, chatbots o experiencias omnicanal
- riesgo de depender de cómo esté renderizada la web

## 3. Objetivo del producto

Crear una capa API propia que permita:

- consultar prestadores con filtros potentes
- buscar por texto libre con buena relevancia
- navegar regiones, localidades, tipos, especialidades y estudios
- devolver respuestas limpias y consistentes
- desacoplar el producto final del frontend actual de OSMEDICA
- operar bajo dominio propio

## 4. Objetivos concretos

### Fase 1

- consumir y normalizar la fuente pública actual
- exponer una API REST propia
- soportar búsqueda por texto
- soportar filtros por:
  - tipo de prestador
  - especialidad
  - estudio
  - región
  - localidad
- exponer facetas / conteos por filtro
- definir pipeline de sincronización

### Fase 2

- agregar ranking de relevancia más inteligente
- autocompletado
- sinónimos médicos / de uso común
- respuestas optimizadas para chatbots
- caché y observabilidad

### Fase 3

- enriquecer con campos adicionales si aparece nueva fuente
- recomendaciones / relacionados
- geolocalización si hay coordenadas
- panel interno de administración o QA de datos

## 5. Usuarios

### Usuario final
Persona que quiere encontrar rápidamente un prestador, centro, estudio, farmacia, óptica o guardia.

### Usuario interno / producto
Equipo que quiere construir:

- sitio o landing propia
- buscador moderno
- chatbot asistido
- integraciones internas
- experiencias móviles

## 6. Casos de uso

- buscar "cardiólogo en Quilmes"
- listar farmacias en GBA Sur
- encontrar guardia odontológica por zona
- mostrar especialidades disponibles en una localidad
- alimentar un chatbot que responda consultas de cartilla
- ofrecer autocompletado de especialidades y ubicaciones

## 7. Requisitos funcionales

### RF-01
La API debe listar prestadores paginados.

### RF-02
La API debe permitir búsqueda por texto libre.

### RF-03
La API debe filtrar por tipo de prestador.

### RF-04
La API debe filtrar por especialidad.

### RF-05
La API debe filtrar por estudio.

### RF-06
La API debe filtrar por región.

### RF-07
La API debe filtrar por localidad.

### RF-08
La API debe devolver facetas/conteos para filtros.

### RF-09
La API debe exponer catálogos auxiliares:

- tipos de prestador
- regiones
- localidades
- especialidades
- estudios

### RF-10
La API debe poder sincronizar datos periódicamente desde la fuente actual.

## 8. Requisitos no funcionales

- respuestas consistentes y versionables
- tiempos de respuesta bajos
- posibilidad de cachear resultados
- trazabilidad del origen de datos
- tolerancia a cambios menores del sitio original
- arquitectura apta para desplegar en dominio propio

## 9. Fuera de alcance inicial

- autenticación compleja
- panel administrativo completo
- edición manual de prestadores
- mapas avanzados
- geolocalización exacta
- scraping visual intensivo del sitio

## 10. Métricas de éxito

- reducción del tiempo para encontrar prestadores relevantes
- mejor tasa de éxito en búsquedas
- menor ambigüedad en filtros
- facilidad de integración con frontend propio y asistentes
- estabilidad del sync con la fuente original

## 11. Riesgos

- cambios en la estructura de la fuente pública WordPress
- ausencia de campos enriquecidos como dirección u horarios
- inconsistencias en taxonomías originales
- datos duplicados o poco homogéneos

## 12. Estrategia inicial recomendada

1. construir capa de ingesta desde WordPress REST API
2. normalizar estructura
3. indexar en base propia
4. exponer REST API propia
5. agregar búsqueda y facetas
6. iterar relevancia y UX
