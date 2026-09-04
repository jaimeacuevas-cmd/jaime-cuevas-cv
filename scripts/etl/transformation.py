"""Data transformation module - maps 12 sheets to unified node/link model."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .utils import (
    validate_orcid, validate_wikidata_qid, validate_id_format,
    validate_coordinates, normalize_na_values, normalize_url, normalize_period
)

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms raw Excel rows into unified CIDOC-CRM node/link structure."""

    def __init__(self):
        """Initialize transformer with empty state."""
        self.nodes = []
        self.links = []
        self.node_ids = set()
        self.errors = []

    def transform(self, raw_entities: Dict[str, List[Dict]], relations_raw: Optional[List[Dict]] = None):
        """
        Main transformation entry point.
        Input: dict of entity type → rows
        Output: (nodes, links)
        """
        # Transform entity sheets
        for entity_type, rows in raw_entities.items():
            transformer_method = getattr(self, f'_transform_{entity_type.lower()}', None)
            if transformer_method:
                logger.info(f"Transforming {entity_type}: {len(rows)} rows")
                try:
                    entities = transformer_method(rows)
                    self.nodes.extend(entities)
                    logger.info(f"  → {len(entities)} nodes created")
                except Exception as e:
                    logger.error(f"Error transforming {entity_type}: {e}")
                    self.errors.append(f"{entity_type}: {e}")

        # Track node IDs for FK validation later
        for node in self.nodes:
            self.node_ids.add(node['id'])

        # Transform links from relations sheet
        if relations_raw:
            relation_links = self._transform_links(relations_raw)
            self.links.extend(relation_links)
            logger.info(f"Transformed relations: {len(relation_links)} links from relations sheet, total: {len(self.links)} links")

        logger.info(f"Total nodes after transformation: {len(self.nodes)}")

        return self.nodes, self.links

    def _create_base_node(self, entity_type: str, row: Dict, row_idx: int) -> Dict[str, Any]:
        """Create base node with common fields."""
        node_id = validate_id_format(entity_type, row_idx + 1)

        return {
            'id': node_id,
            'type': entity_type,
            'label': str(row.get('label', '')).strip(),
            'short_name': str(row.get('short_name', '')).strip() or None,
            'category': str(row.get('category', '')).strip() or None,
            'description': str(row.get('description', '')).strip() or None,
            'url': normalize_url(row.get('url')),
            'is_core': bool(row.get('is_core', False)),
            'source_sheet': row.get('_sheet_name', ''),
            'row_number': row_idx + 1,
        }

    def _transform_agent(self, rows: List[Dict]) -> List[Dict]:
        """Transform Agentes_y_Artistas → Agent nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Agent', row, idx)

            # Agent-specific fields (using snake_case column names from Excel)
            node.update({
                'label': row.get('nombre_completo', '').strip(),
                'short_name': row.get('nombre_corto', '').strip() or None,
                'category': row.get('tipo_agente', '').strip() or None,
                'nationality': normalize_na_values(row.get('nacionalidad')),
                'role': row.get('rol_principal', '').strip() or None,
                'period': normalize_period(row.get('periodo_actividad')),
                'orcid': validate_orcid(row.get('orcid')),
                'wikidata': None,  # Persons never have Wikidata QID
                'urls': {
                    'main': normalize_url(row.get('url_perfil_o_bio')),
                    'scholar': normalize_url(row.get('google_scholar_url')),
                    'github': normalize_url(row.get('github_url')),
                    'linkedin': normalize_url(row.get('linkedin_url')),
                    'academia': normalize_url(row.get('academia_edu_url')),
                },
                '_sheet_name': 'Agentes_y_Artistas',
            })

            nodes.append(node)

        return nodes

    def _transform_organization(self, rows: List[Dict]) -> List[Dict]:
        """Transform Organizaciones → Organization nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Organization', row, idx)

            node.update({
                'label': row.get('nombre_oficial', '').strip(),
                'short_name': row.get('sigla', '').strip() or None,
                'category': row.get('tipo_institucion', '').strip() or None,
                'city': row.get('ciudad', '').strip() or None,
                'url': normalize_url(row.get('url_web')),
                'wikidata': validate_wikidata_qid(row.get('wikidata_id')),
                '_sheet_name': 'Organizaciones',
            })

            nodes.append(node)

        return nodes

    def _transform_location(self, rows: List[Dict]) -> List[Dict]:
        """Transform Lugares_y_Sedes → Location nodes (with coordinates)."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Location', row, idx)

            try:
                lon = row.get('longitud')
                lat = row.get('latitud')
                coordinates = validate_coordinates(float(lon) if lon else None, float(lat) if lat else None)
            except Exception as e:
                logger.warning(f"Invalid coordinates for Location {idx}: {e}")
                coordinates = None

            node.update({
                'label': row.get('toponimo', '').strip(),
                'category': row.get('tipo_lugar', '').strip() or None,
                'city': normalize_na_values(row.get('ciudad')),
                'district': normalize_na_values(row.get('comuna_distrito')),
                'coordinates': list(coordinates) if coordinates else None,
                'wikidata': validate_wikidata_qid(row.get('wikidata_id')),
                'description': row.get('descripcion', '').strip() or None,
                'why_relevant': row.get('por_que_relevante', '').strip() or None,
                'micro_summary': row.get('resumen_micro', '').strip() or None,
                'parent_org_id': row.get('parent_org_id') or None,
                'is_user_primary': bool(row.get('is_user_primary', False)),
                'precision_type': row.get('precision_type', 'exact'),
                '_sheet_name': 'Lugares_y_Sedes',
            })

            # Generate ORG→LOC link if parent_org_id is present
            if node['parent_org_id']:
                org_loc_link = {
                    'id': f"REL_ORG_LOC_{idx+1:04d}",
                    'source': node['parent_org_id'],
                    'target': node['id'],
                    'predicate': 'crm:P87_is_identified_by',
                    'description': f"Organization {node['parent_org_id']} has location {node['id']}",
                    '_sheet_name': 'Lugares_y_Sedes_GENERATED',
                }
                self.links.append(org_loc_link)

            nodes.append(node)

        return nodes

    def _transform_education(self, rows: List[Dict]) -> List[Dict]:
        """Transform Formacion_Academica → Education nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Education', row, idx)

            node.update({
                'label': row.get('nombre_programa', '').strip(),
                'category': row.get('nivel_formativo', '').strip() or None,
                'institution': row.get('institucion', '').strip() or None,
                'period': normalize_period(row.get('periodo')),
                'field': row.get('campo_estudio', '').strip() or None,
                '_sheet_name': 'Formacion_Academica',
            })

            nodes.append(node)

        return nodes

    def _transform_position(self, rows: List[Dict]) -> List[Dict]:
        """Transform Trayectoria_Laboral → Position nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Position', row, idx)

            node.update({
                'label': row.get('cargo_o_rol', '').strip(),
                'organization': row.get('institucion', '').strip() or None,
                'period': normalize_period(row.get('periodo')),
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Trayectoria_Laboral',
            })

            nodes.append(node)

        return nodes

    def _transform_publication(self, rows: List[Dict]) -> List[Dict]:
        """Transform Publicaciones → Publication nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Publication', row, idx)

            node.update({
                'label': row.get('titulo_publicacion', '').strip(),
                'category': row.get('tipo_publicacion', '').strip() or None,
                'authors': row.get('coautores_editores', '').strip() or None,
                'year': int(row.get('ano', 0)) if row.get('ano') else None,
                'url': normalize_url(row.get('doi_o_url')),
                'description': row.get('resumen', '').strip() or None,
                '_sheet_name': 'Publicaciones',
            })

            nodes.append(node)

        return nodes

    def _transform_exhibition(self, rows: List[Dict]) -> List[Dict]:
        """Transform Exposiciones_Curadurias → Exhibition nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Exhibition', row, idx)

            node.update({
                'label': row.get('titulo_exposicion', '').strip(),
                'location': row.get('lugar', '').strip() or None,
                'period': normalize_period(row.get('periodo')),
                'role': row.get('rol_desempenado', '').strip() or None,
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Exposiciones_Curadurias',
            })

            nodes.append(node)

        return nodes

    def _transform_project(self, rows: List[Dict]) -> List[Dict]:
        """Transform Proyectos_y_Fondos → Project nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Project', row, idx)

            node.update({
                'label': row.get('nombre_proyecto_o_premio', '').strip(),
                'funder': row.get('institucion_agencia_financiamiento', '').strip() or None,
                'period': normalize_period(row.get('periodo')),
                'role': row.get('rol_desempenado', '').strip() or None,
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Proyectos_y_Fondos',
            })

            nodes.append(node)

        return nodes

    def _transform_media(self, rows: List[Dict]) -> List[Dict]:
        """Transform Medios_y_Congresos → Media nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Media', row, idx)

            node.update({
                'label': row.get('tema_titulo', '').strip(),
                'category': row.get('formato', '').strip() or None,
                'event_or_media': row.get('evento_o_medio', '').strip() or None,
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Medios_y_Congresos',
            })

            nodes.append(node)

        return nodes

    def _transform_digitalheritage(self, rows: List[Dict]) -> List[Dict]:
        """Transform Portafolio_Digital_Web → DigitalHeritage nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('DigitalHeritage', row, idx)

            node.update({
                'label': row.get('nombre_proyecto', '').strip(),
                'url': normalize_url(row.get('institucion_o_url')),
                'category': row.get('tipo_proyecto', '').strip() or None,
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Portafolio_Digital_Web',
            })

            nodes.append(node)

        return nodes

    def _transform_concept(self, rows: List[Dict]) -> List[Dict]:
        """Transform Tesauro_SKOS → Concept nodes."""
        nodes = []

        for idx, row in enumerate(rows):
            node = self._create_base_node('Concept', row, idx)

            node.update({
                'label': row.get('termino_preferente', '').strip(),
                'category': 'Concepto',
                'alt_terms': row.get('terminos_alternativos', '').strip() or None,
                'skos_definition': row.get('definicion_alcance', '').strip() or None,
                'aat_getty_uri': row.get('uri_aat_getty', '').strip() or None,
                '_sheet_name': 'Tesauro_SKOS',
            })

            nodes.append(node)

        return nodes

    def _transform_links(self, relations_raw: List[Dict]) -> List[Dict]:
        """Transform Relaciones_Grafo_LOD → link records."""
        links = []

        for idx, row in enumerate(relations_raw):
            link = {
                'id': f"REL_{idx+1:04d}",
                'source': row.get('id_origen', '').strip() or None,
                'target': row.get('id_destino', '').strip() or None,
                'predicate': row.get('predicado_cidoc', 'rdfs:seeAlso').strip(),
                'year': row.get('ano'),
                'description': row.get('descripcion', '').strip() or None,
                '_sheet_name': 'Relaciones_Grafo_LOD',
            }

            # Only add if source and target are present
            if link['source'] and link['target']:
                links.append(link)

        return links
