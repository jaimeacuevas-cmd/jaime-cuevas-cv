# Plan de Mantenimiento - Pipeline Fuente Única

## Resumen Ejecutivo

Este documento establece procedimientos para mantener la salud del proyecto, asegurar integridad de datos, y documentar el historial de cambios en el dataset de Jaime Cuevas.

**Estado Actual** (2026-09-05):
- **274 nodos** (43 agentes, 42 organizaciones, 57 ubicaciones, 30 exhibiciones, 21 proyectos, etc.)
- **265 enlaces** en el grafo de conocimiento
- **226 relaciones explícitas** en Relaciones_Grafo_LOD
- **100% conectividad** de agentes (todos tienen ≥1 relación)

---

## 1. GESTIÓN DEL HISTORIAL DE CAMBIOS

### Estructura de Commits

Todos los commits deben seguir este formato:

```
[CATEGORÍA] Título breve (máx 60 caracteres)

Descripción detallada:
- Qué fue añadido/modificado/corregido
- Por qué se realizó el cambio
- Impacto en la red (nodos, enlaces, relaciones)
- Fuente de verificación (abstract, catálogo, institución)

Métricas antes/después:
- Nodos: X → Y
- Enlaces: X → Y
- Relaciones: X → Y

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

### Categorías de Commits

- **[DATA]**: Cambios en CV_Dataset_Maestro (agentes, relaciones, proyectos)
- **[ETL]**: Cambios en scripts (ingestion, transformation, validation, build)
- **[FIX]**: Correcciones de data integrity (QIDs, ORCIDs, coordinates)
- **[SCHEMA]**: Cambios en estructura Excel o propiedades de nodos
- **[DOCS]**: Documentación, guías, changelog

### Versionado Semántico

- **v1.1.0** (Dessilotization phase): Gloria Cortés + 56 relaciones basadas en abstracts
- **v1.2.0** (Próximo): Nuevas entidades/relaciones significativas
- **v2.0.0** (Futuro): Cambios estructurales en modelo de datos

Crear tags: `git tag -a v1.1.0 -m "Release 1.1.0"`

---

## 2. DOCUMENTACIÓN REQUERIDA

### 2.1 Changelog (CHANGELOG.md)

Se mantiene en la raíz. Actualizar con cada cambio significativo:

```markdown
## [1.1.0] - 2026-09-05
### Added
- Gloria Cortés (PER_0002) como investigadora/editora
- 56 nuevas relaciones basadas en abstracts
- 2 nuevas entidades: Desacatos exhibition, Callejera Madrid project

### Verified
- 18 publication abstracts analizados
- 30 exhibition catalogs referenciados
- 226 relaciones explícitas documentadas
```

### 2.2 Data Dictionary (DATA_DICTIONARY.md)

Documente campos Excel clave:

```markdown
## Agentes_y_Artistas
- **id_agente**: PER_NNNN, código único
- **nombre_completo**: Nombre legal
- **orcid**: NNNN-NNNN-NNNN-NNN[NX] (validado)
- **wikidata_id**: Q-ID, rechaza Q124618790-Q124618818 (sintéticos)

## Relaciones_Grafo_LOD
- **id_relacion**: REL_NNNN, secuencial
- **predicado_cidoc**: crm:P14i_performed, crm:P129_subject_of, etc.
- **descripcion_semantica**: Fuente de la relación
```

### 2.3 Scripts README (scripts/etl/README.md)

Documente cómo funciona el pipeline.

---

## 3. PROCEDIMIENTO PARA NUEVAS ADICIONES

### Flujo: Agregar Nuevo Agente

```
1. VERIFICACIÓN PREVIA
   □ ¿Persona real o entidad documentada?
   □ ¿Hay fuente (publicación, catálogo)?
   □ ¿Qué relación con PER_0001 (Jaime)?

2. REGISTRO EN EXCEL
   □ Determinar PER_NNNN (buscar gap)
   □ Campos obligatorios: nombre_completo, rol_principal, tipo_agente
   □ Buscar ORCID en https://orcid.org/
   □ Buscar Wikidata Q-ID en https://www.wikidata.org/

3. CREAR RELACIÓN
   □ Agregar fila en Relaciones_Grafo_LOD
   □ Usar predicado CIDOC-CRM apropiado
   □ Documentar fuente en descripcion_semantica

4. VALIDAR
   □ python3 scripts/build.py
   □ Verificar 0 errores
   □ Revisar output en dist/data/graph_data.json

5. COMMIT
   □ git add + commit con [DATA] category
   □ Push a rama feature
   □ Crear PR con referencia a fuente
```

### Flujo: Agregar Relación

```
1. IDENTIFICAR FUENTE
   - Publication abstract
   - Exhibition catalog
   - Project description
   - Media/congress event

2. MAPEAR A PREDICADO CIDOC-CRM
   crm:P14i_performed      → Agente participó/realizó
   crm:P129_subject_of     → Agente es sujeto de publicación
   crm:P108_has_produced   → Proyecto produjo artefacto
   crm:P11_had_participant → Agente en evento/exposición

3. AGREGAR A EXCEL
   Relaciones_Grafo_LOD:
   - REL_NNNN (secuencial)
   - id_origen, predicado, id_destino
   - año (exacto o rango: 2023 o 2017-2025)
   - descripcion_semantica con cita

4. VALIDAR & COMMIT
   python3 scripts/build.py
   git add + commit [DATA] Add relations: ...
```

---

## 4. CONTROL DE CALIDAD

### Pre-Commit Checklist

Antes de `git push`:

```bash
# 1. Ejecutar pipeline
python3 scripts/build.py

# 2. Validar métricas
python3 scripts/validate.py

# 3. Verificar idempotencia
python3 scripts/build.py > /tmp/build1.log
python3 scripts/build.py > /tmp/build2.log
diff /tmp/build1.log /tmp/build2.log

# 4. Verificar outputs
python3 -c "import json; g = json.load(open('data/graph_data.json')); assert len(g['nodes']) == 274"
```

### Métricas a Monitorear

| Métrica | Target | Alert |
|---------|--------|-------|
| Total Nodes | 274 | < 270 \| > 280 |
| Total Links | 265 | < 260 \| > 270 |
| Agent Connectivity | 100% (43/43) | < 95% |
| Network Density | 0.71% | < 0.6% \| > 1.0% |
| Build Warnings | < 150 | > 200 |
| Validation Errors | 0 | > 0 |

### Auditoría Trimestral

Cada 3 meses:

```
□ Revisar commits del trimestre
□ Verificar fuentes de nuevas relaciones
□ Actualizar CHANGELOG
□ Detectar silos emergentes
□ Validar QID sintético ausente
□ Generar reporte de cobertura (% ORCID, Wikidata)
```

---

## 5. GOBIERNO DE COLABORACIÓN

### Git Workflow

```
1. Crear rama feature:
   git checkout -b feature/descripcion-bhfyhg

2. Hacer cambios en Excel y scripts

3. Ejecutar validaciones (ver 4. Control de Calidad)

4. Commit + Push:
   git add data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx data/graph_data.json ...
   git commit -m "[DATA] Descripción detallada"
   git push -u origin feature/descripcion-bhfyhg

5. Crear PR en GitHub con:
   - Referencia a contexto/issue
   - Métricas antes/después
   - Fuentes de nuevas relaciones
```

### Code Review Checklist

```
□ ¿Nuevas relaciones tienen fuente documentada?
□ ¿Nuevos agentes en Excel (no solo comentarios)?
□ ¿Build.py ejecutado exitosamente?
□ ¿Sin QIDs sintéticos en output?
□ ¿Fechas en formato correcto?
□ ¿CHANGELOG actualizado?
```

---

## 6. RECUPERACIÓN DE ERRORES

### Si comete error en Excel

```bash
# 1. Ver historial
git log --oneline data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx

# 2. Restaurar versión anterior
git checkout <commit> -- data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx

# 3. Rerun build
python3 scripts/build.py

# 4. Commit corrección
git commit -m "[FIX] Revert Excel to <commit>"
```

### Si build falla

```
1. Revisar output de build.py (errores en rojo)
2. Abrir data/validation_report.json
3. Identificar fila problemática
4. Corregir en Excel
5. Rerun python3 scripts/build.py
```

---

## 7. MONITOREO POST-DEPLOY

Después de merge a main:

```bash
# Verificar GitHub Pages actualizado
curl -s https://jaimeacuevas-cmd.github.io/jaime-cuevas-cv/data/graph_data.json | jq '.nodes | length'
# Debe retornar: 274

# Abrir en navegador y verificar:
# - D3 graph carga sin errores console
# - Leaflet map renderiza features
# - Botón "Export LOD" descarga TTL
```

---

## 8. VERSIONADO DE ESQUEMA

### Schema de Nodos (data/schema_jaime_cuevas.json)

```json
{
  "version": "1.1.0",
  "updated_at": "2026-09-05",
  "node_types": {
    "Agent": {
      "fields": ["id", "label", "role", "orcid", "wikidata"],
      "cidoc_class": "E21_Person"
    }
  }
}
```

Actualizar versión cuando:
- Se agreguen nuevos campos obligatorios
- Se cambien tipos de datos
- Se deprecen predicados

---

## 9. CHECKLIST MENSUAL

```
□ Revisar commits del mes
□ Ejecutar: python3 scripts/validate.py
□ Revisar: data/validation_report.json
□ Actualizar: CHANGELOG.md
□ Verificar: GitHub Pages deploys
□ Backup: Todo committed en main
```

---

## REFERENCIAS

- **CIDOC-CRM**: http://cidoc-crm.org/
- **Wikidata**: https://www.wikidata.org/
- **ORCID**: https://orcid.org/
- **RDF/Turtle**: https://www.w3.org/TR/turtle/
- **GeoJSON**: https://tools.ietf.org/html/rfc7946

---

*Última actualización: 2026-09-05*
*Responsable: Jaime Arnaldo Cuevas Pérez*
