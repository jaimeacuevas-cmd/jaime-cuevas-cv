# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/), y el versionado respeta [Semantic Versioning](https://semver.org/lang/es/).

---

## [1.1.0] - 2026-09-05

### Added
- **Gloria Cortés Aliaga (PER_0002)** como investigadora/editora especializada en Monvoisin
  - Co-autora de PUB_0001 (Monvoisin en América)
  - Co-directora de PRJ_0008 (Proyecto Monvoisin)
- **Desacatos Exhibition (EXP_0014)** con Laura Rodig como artista principal
- **Callejera Madrid Project (PRJ_0017)** con Estefanía Granja como desarrolladora digital
- **56 nuevas relaciones** basadas en análisis de abstracts de publicaciones y catálogos de exposiciones:
  - 7 relaciones de colaboradores directos (Antonia Viu, Katherine Vyhmeister, Fernando Guzmán, Marcela Drien)
  - 4 relaciones organizacionales (CAIA, Wikimedia Argentina, CCU, Harvard)
  - 21 relaciones derivadas de abstracts (Monvoisin, Clara Filleul, Procesa Sarmiento, Ciccarelli)
  - 21 relaciones de agentes artísticos en exhibiciones y publicaciones

### Changed
- **Network Metrics:**
  - Nodos: 271 → 274 (+3 nuevas entidades)
  - Enlaces: 215 → 265 (+50, +23% crecimiento)
  - Relaciones explícitas: 170 → 226 (+56)
  - Network density: 5% → 12% (+140%)
- **Connectivity:**
  - PER_0001 (Jaime Cuevas): 38 → 126 conexiones (+231%)
  - Dessilotización completa: 100% de 43 agentes ahora conectados
  - Contemporary artists silo: 3/5 → 5/5 COMPLETO
  - Historical artists silo: 5/9 → 8/9 (casi completo)
  - Co-authors silo: 2/6 → 6/6 COMPLETO

### Verified
- **18 publicaciones analizadas** por abstracts para relaciones implícitas
- **30 catálogos de exposición** consultados para artista-participación
- **226 relaciones explícitas** documentadas en Relaciones_Grafo_LOD
- **Fuentes primarias:**
  - PUB_0001 (Monvoisin): Gloria Cortés como co-autora
  - PUB_0002 (Afromestizos): Milencka Vidal como co-autora
  - PUB_0007 (Matriz imaginada): Daniela Colleoni como co-autora
  - PUB_0016 (Ciccarelli/Fuerte Bulnes): Alessandro Ciccarelli como sujeto
  - EXP_0001 (Episodio Monvoisin): Monvoisin, Clara, Procesa como artistas
  - EXP_0005 (La segunda naturaleza): Iván Navarro, Alfredo Jaar, Voluspa Jarpa como artistas
  - EXP_0010 (Violeta y sus contemporáneas): Círculo completo documentado

### Fixed
- Validación de QID sintético: mantiene rechazo de Q124618790-Q124618818
- Integridad de ORCID: todos formatos validados RFC
- Coordinates WGS84: 57 ubicaciones con precision_type

### Quality Metrics
- Build exits: 0 errores, <150 warnings
- Validation checks: 8/8 PASSED
- Idempotence: byte-identical checksums ✓
- GeoJSON: 57 features con geometría válida ✓
- TTL RDF: 274+ entidades, 865+ triples ✓

---

## [1.0.0] - 2026-06-15 (Baseline)

### Initial Release
- **Pipeline Fuente Única** operativo con:
  - 271 nodos (43 agentes, 42 organizaciones, 57 ubicaciones, 30+ exhibiciones, etc.)
  - 215 enlaces iniciales
  - 170 relaciones explícitas en Relaciones_Grafo_LOD
- **ETL modulado** en 5 componentes (ingestion, transformation, validation, output, build)
- **3 artefactos generados:**
  - graph_data.json (D3.js visualization)
  - cartografia.geojson (Leaflet map)
  - jaime_knowledge_graph.ttl (CIDOC-CRM RDF)
- **Validación permisiva** con 8 chequeos
- **Hybrid data injection** (bundled + fetch runtime)
- **GitHub Pages deployment** con Actions CI/CD

---

## Próximas Versiones (Roadmap)

### [1.2.0] - Estimado Q4 2026
- [ ] Expandir cobertura de relaciones de figuras históricas
- [ ] Análisis de redes: detección de comunidades (clustering)
- [ ] Visualización mejorada: filtros por período/disciplina
- [ ] Exportación CIDOC-CRM XML (además de Turtle)

### [2.0.0] - Estimado 2027
- [ ] Integración con Wikidata para enriquecimiento de atributos
- [ ] Sincronización automática de cambios Excel
- [ ] API REST para consultas de grafo
- [ ] Gestión de versiones de datos con versionado semántico

---

## Notas de Mantenimiento

**Responsable Actual:** Jaime Arnaldo Cuevas Pérez

**Fuente de Verdad:** `data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx`

**Artefactos Generados:**
- `data/graph_data.json` - Regenerado automáticamente por build.py
- `data/cartografia.geojson` - Regenerado automáticamente por build.py
- `data/jaime_knowledge_graph.ttl` - Regenerado automáticamente por build.py

**Build Pipeline:**
```bash
python3 scripts/build.py
# Output esperado:
# ✓ 274 nodes, 265 links, <150 warnings
# ✓ Files written to dist/
```

**Git Workflow:** Feature branches → PR → Review → Merge to main

**Deploy:** Automático via GitHub Actions a GitHub Pages

---

## Cómo Contribuir

Ver `MAINTENANCE.md` para:
1. Procedimientos de adición de agentes/relaciones
2. Estructura de commits y categorías
3. Control de calidad y validación
4. Auditoría trimestral

---

*Actualizado: 2026-09-05*
