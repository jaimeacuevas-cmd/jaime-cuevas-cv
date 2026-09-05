# Data Dictionary

Especificación completa de la estructura de `CV_Dataset_Maestro_Jaime_Cuevas.xlsx` y sus relaciones con los artefactos generados.

---

## Agentes_y_Artistas (Hoja 1)

Tabla: **43 filas** (PER_0001 a PER_0043, con PER_0002 agregado en v1.1.0)

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| **id_agente** | String(10) | ✓ SÍ | Identificador único. Formato: `PER_NNNN` | PER_0001 |
| **nombre_completo** | String(255) | ✓ SÍ | Nombre legal completo del agente | Jaime Arnaldo Cuevas Pérez |
| **nombre_corto** | String(50) | ✗ OPCIONAL | Etiqueta para visualización en grafo | Jaime Cuevas |
| **rol_principal** | String(200) | ✓ SÍ | Descripción de rol/roles (separados por `\|`) | Historiador del Arte \| Curador |
| **tipo_agente** | Enum | ✓ SÍ | Tipo de entidad: `Persona` \| `Organización` \| `Institución` | Persona |
| **nacionalidad** | String(50) | ✗ OPCIONAL | País de nacionalidad o afiliación | Chilena |
| **periodo_actividad** | String(50) | ✗ OPCIONAL | Período de actividad: `YYYY-presente` o `YYYY-YYYY` | 2005-presente |
| **orcid** | String(19) | ✗ OPCIONAL | ORCID código (validado RFC). **Formato exacto:** `NNNN-NNNN-NNNN-NNN[NX]` | 0000-0002-2563-6676 |
| **url_perfil_o_bio** | String(500) | ✗ OPCIONAL | URL a sitio web, perfil académico, o biografía | https://scholar.google.com/... |
| **wikidata_id** | String(20) | ✗ OPCIONAL | Identificador Wikidata. **Formato:** `Q12345678`. **RECHAZADO:** Q124618790-Q124618818 (sintéticos) | Q1234567 |

### Validaciones
- **id_agente**: Único, sin duplicados
- **orcid**: Matching regex `^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$` O vacío
- **wikidata_id**: Q-ID válido, NO sintético (< Q124618790 o > Q124618818)
- **tipo_agente**: Solo valores enumerados

---

## Organizaciones (Hoja 2)

Tabla: **42 filas** (ORG_0001 a ORG_0042)

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| **id_organizacion** | String(10) | ✓ SÍ | Formato: `ORG_NNNN` | ORG_0001 |
| **nombre_organizacion** | String(255) | ✓ SÍ | Nombre oficial de la institución | Museo de Arte Contemporáneo |
| **nombre_corto** | String(50) | ✗ OPCIONAL | Acrónimo para visualización | MAC |
| **tipo_organizacion** | Enum | ✓ SÍ | Tipo: `Museo` \| `Galería` \| `Universidad` \| `Fundación` \| `Archivo` \| etc. | Museo |
| **pais_ciudad** | String(100) | ✗ OPCIONAL | Ubicación: "País, Ciudad" | Chile, Santiago |
| **wikidata_id** | String(20) | ✗ OPCIONAL | Q-ID en Wikidata | Q... |
| **url_oficial** | String(500) | ✗ OPCIONAL | Sitio web oficial | https://www.macmuseo.cl/ |
| **ano_fundacion** | Integer | ✗ OPCIONAL | Año de fundación | 1995 |

---

## Lugares_y_Sedes (Hoja 3)

Tabla: **57 filas** (LOC_0001 a LOC_0057)

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| **id_lugar** | String(10) | ✓ SÍ | Formato: `LOC_NNNN` | LOC_0001 |
| **nombre_lugar** | String(255) | ✓ SÍ | Nombre del lugar/sede | Quinta Normal, Santiago |
| **nombre_corto** | String(50) | ✗ OPCIONAL | Etiqueta breve | Quinta Normal |
| **tipo_lugar** | Enum | ✓ SÍ | `Museo` \| `Galería` \| `Universidad` \| `Biblioteca` \| `Plaza` \| etc. | Museo |
| **pais_ciudad** | String(100) | ✗ OPCIONAL | País y ciudad | Chile, Santiago |
| **coordenadas_lat** | Float | ✓ SÍ | Latitud WGS84 (-90 a 90) | -33.4352 |
| **coordenadas_lon** | Float | ✓ SÍ | Longitud WGS84 (-180 a 180) | -70.6439 |
| **precision_type** | Enum | ✗ OPCIONAL | Nivel de precisión: `exact` \| `centroid` \| `approximate` | centroid |
| **parent_org_id** | String(10) | ✗ OPCIONAL | Referencia a organización madre (FK a ORG_NNNN) | ORG_0001 |
| **is_user_primary** | Boolean | ✗ OPCIONAL | ¿Ubicación principal del usuario? | TRUE |
| **wikidata_id** | String(20) | ✗ OPCIONAL | Q-ID en Wikidata | Q... |
| **url_ubicacion** | String(500) | ✗ OPCIONAL | Google Maps, Wikipedia, etc. | https://maps.google.com/... |
| **notas** | Text | ✗ OPCIONAL | Notas contextuales | Fundada en 1813... |

### Validaciones
- **coordenadas_lat**: -90 ≤ lat ≤ 90
- **coordenadas_lon**: -180 ≤ lon ≤ 180
- **precision_type**: Solo {exact, centroid, approximate}
- **parent_org_id**: FK válido o vacío

---

## Relaciones_Grafo_LOD (Hoja 12)

Tabla: **226 filas** (REL_0001 a REL_0226)

**Hoja CRÍTICA:** Define todas las relaciones explícitas del grafo.

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| **id_relacion** | String(10) | ✓ SÍ | Identificador único. Formato: `REL_NNNN` (secuencial) | REL_0001 |
| **id_origen** | String(10) | ✓ SÍ | ID de nodo origen (PER_, ORG_, LOC_, EXP_, PRJ_, PUB_, etc.) | PER_0001 |
| **predicado_cidoc** | String(50) | ✓ SÍ | CIDOC-CRM predicate. **Opciones comunes:** | crm:P14i_performed |
| | | | `crm:P14i_performed` - Agente participó/realizó | |
| | | | `crm:P129_subject_of` - Sujeto de documento/publicación | |
| | | | `crm:P108_has_produced` - Proyecto produjo artefacto | |
| | | | `crm:P11_had_participant` - Participante en evento | |
| | | | `crm:P87_is_identified_by` - Identificación geográfica | |
| **id_destino** | String(10) | ✓ SÍ | ID de nodo destino (mismo patrón que origen) | PRJ_0008 |
| **ano** | String(20) | ✗ OPCIONAL | Año exacto o rango. **Formatos válidos:** | 2023 |
| | | | Año exacto: `2023` | o |
| | | | Rango: `2017-2025` | |
| | | | Década: `2010s` | |
| **descripcion_semantica** | Text | ✗ OPCIONAL | Descripción de la relación con cita/fuente | Jaime Cuevas co-dirige Monvoisin en América desde 2017 |

### Validaciones
- **id_origen, id_destino**: Deben existir en sus respectivas tablas (integridad referencial)
- **predicado_cidoc**: Debe ser CIDOC-CRM válido (http://cidoc-crm.org/)
- **ano**: Formato `YYYY` o `YYYY-YYYY`, no vacío para relaciones importantes

### Predicados CIDOC-CRM Comunes

| Predicado | Significado | Uso |
|-----------|-------------|-----|
| `crm:P14i_performed` | Agente realizó/participó en | Personas en proyectos, exhibitions |
| `crm:P129_subject_of` | Objeto es sujeto de documento | Personas como sujetos de publicaciones |
| `crm:P108_has_produced` | Proyecto produjo | Proyectos que generan publicaciones/catálogos |
| `crm:P11_had_participant` | Evento tuvo participante | Exhibiciones con artistas/curadores |
| `crm:P87_is_identified_by` | Identificado por | Lugares con coordenadas |

---

## Publicaciones (Hoja 7)

Tabla: **18 filas** (PUB_0001 a PUB_0018)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| **id_publicacion** | String(10) | ✓ SÍ | Formato: `PUB_NNNN` |
| **id_agente** | String(10) | ✓ SÍ | Autor principal (FK a PER_NNNN) |
| **tipo_publicacion** | String(100) | ✓ SÍ | Libro, Capítulo, Artículo, Catálogo, etc. |
| **titulo_publicacion** | String(500) | ✓ SÍ | Título completo |
| **coautores_editores** | Text | ✗ OPCIONAL | Nombres separados por `\|` |
| **abstract_resumen** | Text | ✗ OPCIONAL | **CRÍTICO para análisis de relaciones implícitas** |
| **palabras_clave** | Text | ✗ OPCIONAL | Keywords separadas por `\|` (usadas para descubrimiento) |
| **ano** | Integer | ✓ SÍ | Año de publicación |

### Uso para Relaciones
Los abstracts se analizan para identificar:
- Artistas/agentes mencionados
- Temas/proyectos relacionados
- Conexiones implícitas con otros agentes

---

## Exposiciones_Curadurias (Hoja 8)

Tabla: **30 filas** (EXP_0001 a EXP_0014)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| **id_exposicion** | String(10) | ✓ SÍ | Formato: `EXP_NNNN` o `EXP_NNNN_MNN` (sub-exposiciones) |
| **id_agente** | String(10) | ✓ SÍ | Curador/productor principal |
| **titulo_exposicion** | String(300) | ✓ SÍ | Título oficial |
| **id_artistas_involucrados** | Text | ✗ OPCIONAL | IDs separados por `\|`: `PER_0015 \| PER_0016 \| ...` |
| **institucion_lugar** | String(200) | ✓ SÍ | Nombre de institución/galería |
| **ano** | Integer | ✓ SÍ | Año de realización |
| **texto_curatorial_resumen** | Text | ✗ OPCIONAL | Resumen curatorial (fuente para análisis de relaciones) |

### Uso para Relaciones
Los catálogos y descripciones cuatoriales se usan para:
- Conectar artistas a exhibiciones
- Descubrir influencias y círculos artísticos
- Verificar participación de agentes

---

## Proyectos_y_Fondos (Hoja 9)

Tabla: **21 filas** (PRJ_0001 a PRJ_0017)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| **id_proyecto** | String(10) | ✓ SÍ | Formato: `PRJ_NNNN` |
| **id_agente** | String(10) | ✓ SÍ | Investigador/responsable principal |
| **rol_desempenado** | String(100) | ✓ SÍ | Rol: Investigador Responsable, Asistente, Co-investigador, etc. |
| **nombre_proyecto_o_premio** | String(300) | ✓ SÍ | Nombre oficial del proyecto o beca |
| **institucion_agencia_financiamiento** | String(200) | ✓ SÍ | FONDART, FONDECYT, TYPA, etc. |
| **id_organizacion_financiera** | String(10) | ✗ OPCIONAL | FK a ORG_NNNN |
| **ano_adjudicacion** | Integer | ✓ SÍ | Año de adjudicación |

---

## Tesauro_SKOS (Hoja 4)

Tabla: **21 filas** (CONC_0001 a CONC_0021)

Conceptos y términos de clasificación. Usados para enriquecimiento semántico.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **id_concepto** | String(10) | Formato: `CONC_NNNN` |
| **termino_preferido** | String(100) | Término SKOS preferido |
| **terminos_alternativos** | Text | Sinónimos (separados por `\|`) |
| **definicion** | Text | Definición del concepto |

---

## Artefactos Generados

Estos archivos se generan automáticamente por `scripts/build.py`:

### data/graph_data.json

```json
{
  "nodes": [
    {
      "id": "PER_0001",
      "type": "Agent",
      "label": "Jaime Arnaldo Cuevas Pérez",
      "category": "Persona",
      "role": "Historiador del Arte | Curador",
      "orcid": "0000-0002-2563-6676",
      "wikidata": null,
      "is_core": true
    },
    ...
  ],
  "links": [
    {
      "id": "REL_0001",
      "source": "PER_0001",
      "target": "PRJ_0008",
      "predicate": "crm:P14i_performed",
      "year": "2017-2025",
      "description": "Co-dirige proyecto internacional Monvoisin en América"
    },
    ...
  ]
}
```

**Tabla resumen:**
- **nodes**: 274 entidades de 11 tipos
- **links**: 265 conexiones explícitas + derivadas

### data/cartografia.geojson

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "LOC_0001",
      "geometry": {
        "type": "Point",
        "coordinates": [-70.6439, -33.4352]
      },
      "properties": {
        "name": "Quinta Normal, Santiago",
        "type": "Museum",
        "precision": "centroid",
        "parent_org": "ORG_0001",
        "is_user_primary": true
      }
    }
  ]
}
```

**57 features** geoespaciales (Point/LineString) con WGS84

### data/jaime_knowledge_graph.ttl

```turtle
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix schema: <https://schema.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix geo: <http://www.opengis.net/ont/sf#> .

<jaime:PER_0001> a crm:E21_Person ;
  rdfs:label "Jaime Arnaldo Cuevas Pérez" ;
  schema:identifier "0000-0002-2563-6676" ;
  crm:P14i_performed <jaime:PRJ_0008> .

<jaime:PRJ_0008> a crm:E7_Activity ;
  rdfs:label "Monvoisin en América" ;
  crm:P108_has_produced <jaime:PUB_0001> .
```

**865+ triples RDF** en formato Turtle con CIDOC-CRM

---

## Integridad Referencial

Validaciones clave:

1. **FK en Relaciones_Grafo_LOD**: `id_origen` e `id_destino` deben existir
2. **FK en Lugares**: `parent_org_id` debe ser válido ORG_NNNN o vacío
3. **Unicidad**: Todos los IDs deben ser únicos dentro de su tipo
4. **Secuencia**: IDs REL_NNNN son secuenciales sin gaps

---

## Control de Calidad

### Build Validation
```bash
python3 scripts/build.py
# Esperado:
# ✓ 274 nodes
# ✓ 265 links
# ✓ <150 warnings
# ✓ 0 errors
```

### Checks Automáticos
1. ✓ ID format validation
2. ✓ ORCID RFC format check
3. ✓ Wikidata Q-ID validation (rechazo de sintéticos)
4. ✓ Geographic coordinate bounds
5. ✓ Referential integrity
6. ✓ Duplicate detection

---

## Referencias

- **CIDOC-CRM**: http://cidoc-crm.org/
- **SKOS**: https://www.w3.org/TR/skos-reference/
- **RDF/Turtle**: https://www.w3.org/TR/turtle/
- **GeoJSON**: https://tools.ietf.org/html/rfc7946
- **Wikidata**: https://www.wikidata.org/
- **ORCID**: https://orcid.org/

---

*Versión: 1.1.0 - Actualizado: 2026-09-05*
