"""Output generation module - creates graph_data.json, cartografia.geojson, and TTL."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Generates output artifacts in JSON, GeoJSON, and Turtle formats."""

    CIDOC_CRM_PREDICATES = {
        'Agent→Education': 'crm:P14i_performed',  # Person performed education activity
        'Agent→Position': 'crm:P14i_performed',  # Person performed work activity
        'Agent→Exhibition': 'crm:P14i_performed',  # Person curated exhibition
        'Agent→Publication': 'crm:P108_has_produced',  # Person produced publication
        'Agent→Project': 'crm:P14i_performed',  # Person performed project
        'Organization→Agent': 'crm:P14_carried_out_by',  # Org was carried out by person
        'Organization→Location': 'crm:P74_has_current_or_former_residence',  # Org has location
        'Exhibition→Location': 'crm:P7_took_place_at',  # Exhibition took place at location
    }

    RDF_PREFIXES = {
        'crm': 'http://www.cidoc-crm.org/cidoc-crm/',
        'schema': 'https://schema.org/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'bibo': 'http://purl.org/ontology/bibo/',
        'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'jc': 'https://jaimecuevas.com/resource/',
    }

    CIDOC_ENTITY_CLASSES = {
        'Agent': 'crm:E21_Person',
        'Organization': 'crm:E74_Group',
        'Location': 'crm:E53_Place',
        'Education': 'crm:E7_Activity',
        'Position': 'crm:E7_Activity',
        'Publication': 'crm:E31_Document',
        'Exhibition': 'crm:E7_Activity',
        'Project': 'crm:E7_Activity',
        'Media': 'crm:E7_Activity',
        'DigitalHeritage': 'crm:E73_Information_Object',
        'Concept': 'skos:Concept',
    }

    def __init__(self):
        """Initialize output generator."""
        pass

    def generate_graph_json(self, nodes: List[Dict], links: Optional[List[Dict]], validation_report: Dict) -> Dict:
        """
        Generate graph_data.json for D3.js visualization.
        """
        logger.info("Generating graph_data.json...")

        # Filter out internal fields
        clean_nodes = []
        for node in nodes:
            clean_node = {k: v for k, v in node.items() if not k.startswith('_')}
            clean_nodes.append(clean_node)

        output = {
            'metadata': {
                'version': '2.0',
                'source': 'CV_Dataset_Maestro_Jaime_Cuevas.xlsx',
                'node_count': len(clean_nodes),
                'link_count': len(links) if links else 0,
                'sheet_count': 12,
                'validation_status': validation_report.get('status', 'UNKNOWN'),
                'validation_warnings': validation_report.get('warning_count', 0),
            },
            'nodes': clean_nodes,
            'links': links or [],
        }

        logger.info(f"  ✓ Generated graph with {len(clean_nodes)} nodes and {len(output['links'])} links")
        return output

    def generate_geojson(self, nodes: List[Dict], links: Optional[List[Dict]] = None) -> Dict:
        """
        Generate cartografia.geojson for Leaflet map visualization.
        Only includes Location nodes with coordinates that are connected to Jaime's activities.

        Filtering strategy: A location appears in cartography only if:
        1. It has valid coordinates
        2. It is connected to an organization that Jaime is involved with
        """
        logger.info("Generating cartografia.geojson...")

        # Build Jaime's organization network if links provided
        jaime_orgs = set()
        if links:
            for link in links:
                # Jaime is PER_0001
                if link.get('source') == 'PER_0001':
                    target = link.get('target', '')
                    if target.startswith('ORG_'):
                        jaime_orgs.add(target)
                elif link.get('target') == 'PER_0001':
                    source = link.get('source', '')
                    if source.startswith('ORG_'):
                        jaime_orgs.add(source)
            logger.info(f"  Found {len(jaime_orgs)} organizations connected to Jaime")

        # Build location→org mapping
        loc_to_orgs = {}
        for node in nodes:
            if node.get('type') == 'Location':
                loc_to_orgs[node['id']] = []

        if links:
            for link in links:
                if link.get('source').startswith('LOC_') and link.get('target').startswith('ORG_'):
                    loc_to_orgs[link['source']].append(link['target'])
                elif link.get('target').startswith('LOC_') and link.get('source').startswith('ORG_'):
                    loc_to_orgs[link['target']].append(link['source'])

        # Generate features, filtering by relevance
        features = []
        excluded_count = 0
        for node in nodes:
            if node.get('type') != 'Location':
                continue

            coords = node.get('coordinates')
            if not coords or len(coords) != 2:
                continue

            # Skip location if it has no connection to Jaime's organizations
            loc_id = node.get('id')
            connected_orgs = loc_to_orgs.get(loc_id, [])
            if jaime_orgs and not any(org in jaime_orgs for org in connected_orgs):
                excluded_count += 1
                continue

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': coords,
                },
                'properties': {
                    'id': node.get('id'),
                    'name': node.get('label'),
                    'type': 'Location',
                    'city': node.get('city'),
                    'country': node.get('country'),
                    'wikidata': node.get('wikidata'),
                    'description': node.get('description'),
                    'why_relevant': node.get('why_relevant'),
                    'micro_summary': node.get('micro_summary'),
                    'is_core': node.get('is_core', False),
                    'parent_org_id': node.get('parent_org_id'),
                    'is_user_primary': node.get('is_user_primary', False),
                    'precision_type': node.get('precision_type', 'exact'),
                },
            }

            features.append(feature)

        if excluded_count > 0:
            logger.info(f"  Excluded {excluded_count} locations not connected to Jaime's organizations")

        output = {
            'type': 'FeatureCollection',
            'metadata': {
                'projection': 'WGS84',
                'feature_count': len(features),
                'filtered_count': excluded_count,
            },
            'features': features,
        }

        logger.info(f"  ✓ Generated GeoJSON with {len(features)} location features")
        return output

    def generate_turtle(self, nodes: List[Dict], links: Optional[List[Dict]]) -> str:
        """
        Generate jaime_knowledge_graph.ttl in Turtle/RDF format.
        Uses CIDOC-CRM, Schema.org, and SKOS vocabularies.
        """
        logger.info("Generating jaime_knowledge_graph.ttl...")

        ttl_lines = []

        # Prefixes
        ttl_lines.append('# Generated RDF/Turtle Knowledge Graph')
        ttl_lines.append('# Source: CV_Dataset_Maestro_Jaime_Cuevas.xlsx')
        ttl_lines.append('')
        ttl_lines.append('@prefix crm:    <http://www.cidoc-crm.org/cidoc-crm/> .')
        ttl_lines.append('@prefix schema: <https://schema.org/> .')
        ttl_lines.append('@prefix dc:     <http://purl.org/dc/elements/1.1/> .')
        ttl_lines.append('@prefix bibo:   <http://purl.org/ontology/bibo/> .')
        ttl_lines.append('@prefix geo:    <http://www.w3.org/2003/01/geo/wgs84_pos#> .')
        ttl_lines.append('@prefix skos:   <http://www.w3.org/2004/02/skos/core#> .')
        ttl_lines.append('@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .')
        ttl_lines.append('@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .')
        ttl_lines.append('@prefix jc:     <https://jaimecuevas.com/resource/> .')
        ttl_lines.append('')

        # Entities
        for node in nodes:
            ttl_lines.extend(self._node_to_turtle(node))
            ttl_lines.append('')

        # Links
        if links:
            for link in links:
                ttl_lines.extend(self._link_to_turtle(link))
                ttl_lines.append('')

        ttl_content = '\n'.join(ttl_lines)
        logger.info(f"  ✓ Generated Turtle with {len(nodes)} entities")

        return ttl_content

    def _node_to_turtle(self, node: Dict) -> List[str]:
        """Convert single node to Turtle triples."""
        lines = []
        node_id = node.get('id', 'UNKNOWN')
        entity_type = node.get('type', 'Unknown')
        jc_uri = f"jc:{node_id}"

        # Type declaration
        cidoc_class = self.CIDOC_ENTITY_CLASSES.get(entity_type, 'rdf:Resource')
        lines.append(f"{jc_uri} a {cidoc_class} ;")

        # Label
        label = node.get('label', '')
        if label:
            lines.append(f'    rdfs:label "{self._escape_turtle_string(label)}" ;')

        # Type-specific properties
        if entity_type == 'Agent':
            lines.extend(self._agent_to_turtle_properties(node))
        elif entity_type == 'Organization':
            lines.extend(self._org_to_turtle_properties(node))
        elif entity_type == 'Location':
            lines.extend(self._location_to_turtle_properties(node))
        elif entity_type == 'Publication':
            lines.extend(self._publication_to_turtle_properties(node))
        elif entity_type == 'Concept':
            lines.extend(self._concept_to_turtle_properties(node))

        # Common properties
        description = node.get('description')
        if description:
            lines.append(f'    dc:description "{self._escape_turtle_string(description)}" ;')

        # Remove trailing semicolon from last line
        if lines[-1].endswith(' ;'):
            lines[-1] = lines[-1][:-2] + ' .'
        else:
            lines[-1] += ' .'

        return lines

    def _agent_to_turtle_properties(self, node: Dict) -> List[str]:
        """Generate Turtle properties for Agent node."""
        lines = []

        if node.get('orcid'):
            orcid = node.get('orcid')
            lines.append(f'    skos:exactMatch <https://orcid.org/{orcid}> ;')

        if node.get('urls', {}).get('scholar'):
            lines.append(f'    schema:url <{node["urls"]["scholar"]}> ;')

        if node.get('nationality'):
            lines.append(f'    schema:nationality "{node["nationality"]}" ;')

        return lines

    def _org_to_turtle_properties(self, node: Dict) -> List[str]:
        """Generate Turtle properties for Organization node."""
        lines = []

        if node.get('url'):
            lines.append(f'    schema:url <{node["url"]}> ;')

        if node.get('wikidata'):
            wikidata_url = f"https://www.wikidata.org/wiki/{node['wikidata']}"
            lines.append(f'    skos:exactMatch <{wikidata_url}> ;')

        return lines

    def _location_to_turtle_properties(self, node: Dict) -> List[str]:
        """Generate Turtle properties for Location node."""
        lines = []

        coords = node.get('coordinates')
        if coords and len(coords) == 2:
            lines.append(f'    geo:long {coords[0]} ;')
            lines.append(f'    geo:lat {coords[1]} ;')

        if node.get('city'):
            lines.append(f'    schema:areaServed "{node["city"]}" ;')

        if node.get('wikidata'):
            wikidata_url = f"https://www.wikidata.org/wiki/{node['wikidata']}"
            lines.append(f'    skos:exactMatch <{wikidata_url}> ;')

        return lines

    def _publication_to_turtle_properties(self, node: Dict) -> List[str]:
        """Generate Turtle properties for Publication node."""
        lines = []

        if node.get('year'):
            lines.append(f'    dc:issued "{node["year"]}"^^xsd:gYear ;')

        if node.get('url'):
            lines.append(f'    schema:url <{node["url"]}> ;')

        return lines

    def _concept_to_turtle_properties(self, node: Dict) -> List[str]:
        """Generate Turtle properties for Concept node."""
        lines = []

        definition = node.get('skos_definition')
        if definition:
            lines.append(f'    skos:definition "{self._escape_turtle_string(definition)}" ;')

        return lines

    def _link_to_turtle(self, link: Dict) -> List[str]:
        """Convert single link to Turtle triple."""
        source = link.get('source', 'UNKNOWN')
        target = link.get('target', 'UNKNOWN')
        predicate = link.get('predicate', 'rdfs:seeAlso')

        lines = [
            f"jc:{source} {predicate} jc:{target} .",
        ]

        return lines

    def _escape_turtle_string(self, text: str) -> str:
        """Escape special characters in Turtle string literals."""
        if not isinstance(text, str):
            text = str(text)

        # Escape backslash first
        text = text.replace('\\', '\\\\')
        # Escape double quotes
        text = text.replace('"', '\\"')
        # Escape newlines
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        # Escape tabs
        text = text.replace('\t', '\\t')

        return text
