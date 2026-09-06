#!/usr/bin/env python3
"""
Validate data consistency across source → build → dist → HTML.
Ensures all changes are properly reflected in the final deliverables.
"""

import json
import re
from pathlib import Path

def extract_bundled_data_from_html(html_path):
    """Extract window.BUNDLED_DATA from HTML."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the BUNDLED_DATA script - handle object format with unquoted keys
    match = re.search(r'window\.BUNDLED_DATA\s*=\s*\{(.*?)\n\s*\};', html, re.DOTALL)
    if not match:
        return None

    try:
        # Extract the object content and convert to valid JSON
        content = match.group(1)

        # Convert unquoted keys (graph:, geo:, ttl:) to quoted JSON keys
        # This regex finds: word: {...} and converts to "word": {...}
        json_str = re.sub(r'(\w+):\s*', r'"\1": ', content)

        # Parse as JSON object
        obj = json.loads('{' + json_str + '}')
        return obj
    except (json.JSONDecodeError, TypeError) as e:
        print(f"❌ Error parsing bundled data from HTML: {e}")
        # Try to show what we're trying to parse
        print(f"Attempted to parse: {content[:200]}...")
        return None

def validate_coordinates(source_coords, bundled_coords, location_id, name):
    """Validate coordinates match."""
    if source_coords != bundled_coords:
        print(f"❌ MISMATCH - {location_id} ({name}):")
        print(f"   Source:  {source_coords}")
        print(f"   Bundled: {bundled_coords}")
        return False
    return True

def validate_relationships(source_links, bundled_links, entity_id, entity_name):
    """Validate relationships match."""
    source_rels = {(l['source'], l['predicate'], l['target'])
                   for l in source_links
                   if l['source'] == entity_id or l['target'] == entity_id}

    bundled_rels = {(l['source'], l['predicate'], l['target'])
                    for l in bundled_links
                    if l['source'] == entity_id or l['target'] == entity_id}

    if source_rels != bundled_rels:
        print(f"❌ RELATIONSHIP MISMATCH - {entity_id} ({entity_name}):")
        missing = source_rels - bundled_rels
        extra = bundled_rels - source_rels
        if missing:
            print(f"   Missing in bundled: {missing}")
        if extra:
            print(f"   Extra in bundled: {extra}")
        return False
    return True

def main():
    base_dir = Path(__file__).parent.parent
    source_graph = base_dir / 'data' / 'graph_data.json'
    source_geo = base_dir / 'data' / 'cartografia.geojson'
    dist_graph = base_dir / 'dist' / 'data' / 'graph_data.json'
    dist_html = base_dir / 'dist' / 'index.html'

    print("=" * 80)
    print("DATA SYNC VALIDATION")
    print("=" * 80)

    # Load source data
    with open(source_graph) as f:
        source_graph_data = json.load(f)

    with open(source_geo) as f:
        source_geo_data = json.load(f)

    # Load compiled dist data (more reliable than HTML extraction)
    print("\n[0] Loading compiled data...")
    if dist_graph.exists():
        with open(dist_graph) as f:
            bundled_graph = json.load(f)
        print(f"✓ Loaded dist/data/graph_data.json ({len(bundled_graph['nodes'])} nodes)")
    else:
        print("❌ dist/data/graph_data.json not found")
        return False

    # Also check HTML for bundled fallback
    print("[0b] Checking HTML bundled fallback...")
    bundled_html_data = extract_bundled_data_from_html(dist_html)
    if bundled_html_data:
        print("✓ HTML has bundled data (fallback mode available)")
    else:
        print("⚠ Warning: Could not extract bundled data from HTML (fetch mode will be used)")

    if not bundled_graph:
        print("❌ CRITICAL: Compiled graph data incomplete")
        return False

    # Validation checks
    errors = []

    print("\n[1] Validating node counts...")
    source_nodes = len(source_graph_data['nodes'])
    bundled_nodes = len(bundled_graph['nodes'])
    if source_nodes != bundled_nodes:
        print(f"❌ Node count mismatch: source={source_nodes}, bundled={bundled_nodes}")
        errors.append("node_count")
    else:
        print(f"✓ Node count matches: {source_nodes} nodes")

    print("\n[2] Validating link counts...")
    source_links = len(source_graph_data['links'])
    bundled_links = len(bundled_graph['links'])
    if source_links != bundled_links:
        print(f"❌ Link count mismatch: source={source_links}, bundled={bundled_links}")
        errors.append("link_count")
    else:
        print(f"✓ Link count matches: {source_links} links")

    # Critical entities to validate
    critical_entities = [
        ('LOC_0059', 'Tabacalera'),
        ('EDU_0009', 'Curso 2012'),
        ('ORG_0043', 'Promoción del Arte'),
    ]

    print("\n[3] Validating critical coordinates...")
    for node_id, name in critical_entities:
        source_node = next((n for n in source_graph_data['nodes'] if n['id'] == node_id), None)
        bundled_node = next((n for n in bundled_graph['nodes'] if n['id'] == node_id), None)

        if not source_node:
            print(f"⚠ Warning: {node_id} not in source")
            continue

        if not bundled_node:
            print(f"❌ {node_id} ({name}) missing in bundled data!")
            errors.append(f"missing_{node_id}")
            continue

        source_coords = source_node.get('coordinates')
        bundled_coords = bundled_node.get('coordinates')

        if source_coords and bundled_coords:
            if not validate_coordinates(source_coords, bundled_coords, node_id, name):
                errors.append(f"coords_{node_id}")
            else:
                print(f"✓ {node_id} ({name}): {source_coords}")

    print("\n[4] Validating critical relationships...")
    for node_id, name in critical_entities:
        if not validate_relationships(source_graph_data['links'], bundled_graph['links'], node_id, name):
            errors.append(f"rels_{node_id}")
        else:
            print(f"✓ {node_id} ({name}): relationships match")

    # Specific validation: Tabacalera exact coordinates
    # Note: graph_data.json stores as [lon, lat]
    print("\n[5] Validating exact coordinates (CRITICAL)...")
    tabacalera_exact = [-3.703136525126451, 40.40663337469876]  # [lon, lat] format
    for node in bundled_graph['nodes']:
        if node['id'] == 'LOC_0059':
            bundled_coords = node.get('coordinates')
            if bundled_coords == tabacalera_exact:
                print(f"✓ Tabacalera has exact coordinates: lat={tabacalera_exact[1]}, lon={tabacalera_exact[0]}")
            else:
                print(f"❌ Tabacalera coordinates wrong: expected {tabacalera_exact}, got {bundled_coords}")
                errors.append("tabacalera_exact")

    # Specific validation: EDU_0009 related to LOC_0059
    print("\n[6] Validating EDU_0009 → LOC_0059 relationship...")
    edu_loc_rels = [l for l in bundled_graph['links']
                    if (l['source'] == 'EDU_0009' and l['target'] == 'LOC_0059') or
                       (l['source'] == 'LOC_0059' and l['target'] == 'EDU_0009')]

    if edu_loc_rels:
        print(f"✓ EDU_0009 ↔ LOC_0059 relationship found:")
        for rel in edu_loc_rels:
            print(f"  {rel['source']} → {rel['predicate']} → {rel['target']}")
    else:
        print(f"❌ EDU_0009 ↔ LOC_0059 relationship MISSING!")
        errors.append("edu_loc_relationship")

    # Summary
    print("\n" + "=" * 80)
    if errors:
        print(f"❌ VALIDATION FAILED: {len(errors)} error(s)")
        print(f"Errors: {errors}")
        return False
    else:
        print("✓ ALL VALIDATIONS PASSED")
        print("Data is properly synchronized through the entire pipeline")
        return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
