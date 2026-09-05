#!/usr/bin/env python3
"""
FASE 2: AUDITORÍA DE ETL - Transformation Validation
Tarea 2.1.1 a 2.1.4
"""

import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 80)
print("FASE 2: AUDITORÍA DE ETL - Transformación")
print("=" * 80)

# Task 2.1.1: Test ingestion
print("\n[TAREA 2.1.1] Auditoría de Ingestion")
print("-" * 80)

try:
    from scripts.etl.ingestion import ExcelReader

    reader = ExcelReader('data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx')
    entities = reader.read_all_sheets()

    print(f"✓ Excel ingestion exitoso")

    for entity_type, rows in sorted(entities.items()):
        print(f"  {entity_type}: {len(rows)} rows")

        # Sample first row
        if rows:
            first_row = rows[0]
            cols = list(first_row.keys())[:5]
            print(f"    Columns: {cols}...")

    print("\n[RESULTADO] Ingestion validation:")
    print("✅ PASS - Todas las hojas leídas correctamente")

except Exception as e:
    print(f"❌ ERROR en ingestion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Task 2.1.2: Test transformation
print("\n[TAREA 2.1.2] Auditoría de Transformación")
print("-" * 80)

try:
    from scripts.etl.transformation import DataTransformer

    transformer = DataTransformer()
    nodes, links = transformer.transform(entities)

    print(f"✓ Transformación completada")
    print(f"  Nodos generados: {len(nodes)}")
    print(f"  Links generados: {len(links)}")

    # Count by type
    from collections import Counter
    node_types = Counter(n['type'] for n in nodes)

    print(f"\n  Distribución de nodos:")
    for ntype, count in sorted(node_types.items()):
        print(f"    {ntype}: {count}")

    # Check key nodes exist
    key_nodes = ['PER_0001', 'LOC_0013', 'LOC_0014', 'LOC_0064', 'COM_0011']
    print(f"\n  Nodos clave:")
    node_ids = {n['id'] for n in nodes}
    for key in key_nodes:
        status = "✓" if key in node_ids else "❌"
        print(f"    {status} {key}")

    print("\n[RESULTADO] Transformación validation:")
    if len(nodes) > 200 and len(links) > 500:
        print("✅ PASS - Transformación generó cantidad esperada de nodos/links")
    else:
        print(f"⚠️  PARTIAL - Nodos: {len(nodes)} (esperado ~305), Links: {len(links)} (esperado ~700+)")

except Exception as e:
    print(f"❌ ERROR en transformación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Task 2.1.3: Test implicit links generation
print("\n[TAREA 2.1.3] Auditoría de Links Implícitos")
print("-" * 80)

try:
    implicit_links = [l for l in links if l.get('id', '').startswith('IMPL_')]
    explicit_links = [l for l in links if l.get('id', '').startswith('REL_')]

    print(f"✓ Links implícitos: {len(implicit_links)}")
    print(f"  Links explícitos: {len(explicit_links)}")

    # Check critical implicit links
    event_loc_links = [l for l in implicit_links if l.get('predicate') == 'crm:P7_took_place_at']
    print(f"  Links evento→ubicación (P7_took_place_at): {len(event_loc_links)}")

    # Check for COM_0011 → LOC_0064 specifically
    com_0011_links = [l for l in links if 'COM_0011' in (l.get('source'), l.get('target'))]
    com_0011_to_loc = [l for l in com_0011_links if l['target'].startswith('LOC_')]

    print(f"\n  COM_0011 links:")
    print(f"    Total links involving COM_0011: {len(com_0011_links)}")
    print(f"    COM_0011 → Location links: {len(com_0011_to_loc)}")

    if com_0011_to_loc:
        for link in com_0011_to_loc:
            print(f"      {link['source']} → {link['target']} ({link.get('predicate')})")

    # Check PRJ_0007 links
    prj_0007_links = [l for l in links if 'PRJ_0007' in (l.get('source'), l.get('target'))]
    print(f"\n  PRJ_0007 links: {len(prj_0007_links)}")
    for link in prj_0007_links[:5]:
        print(f"    {link['source']} → {link['target']} ({link.get('predicate')})")

    # Check education→location generation
    edu_nodes = [n for n in nodes if n['type'] == 'Education']
    edu_loc_links = [l for l in implicit_links if any(e['id'] == l['source'] for e in edu_nodes) and l['target'].startswith('LOC_')]

    print(f"\n  Education→Location links: {len(edu_loc_links)}")

    print("\n[RESULTADO] Implicit links validation:")

    # Expected counts
    expected_implicit = 400  # Rough estimate
    expected_event_loc = 100  # Rough estimate

    if len(implicit_links) >= expected_implicit * 0.8:
        print(f"✅ PASS - Implicit links: {len(implicit_links)} (expected ~{expected_implicit})")
    else:
        print(f"⚠️  WARN - Implicit links: {len(implicit_links)} (expected ~{expected_implicit})")

    if len(event_loc_links) >= expected_event_loc * 0.8:
        print(f"✅ PASS - Event→Location links: {len(event_loc_links)} (expected ~{expected_event_loc})")
    else:
        print(f"⚠️  WARN - Event→Location links: {len(event_loc_links)} (expected ~{expected_event_loc})")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Task 2.1.4: Test reachability filtering
print("\n[TAREA 2.1.4] Auditoría de Nodes Reachable (BFS Filtering)")
print("-" * 80)

try:
    from scripts.etl.output_generator import bfs_filter

    # Build adjacency for BFS
    edges = {}
    for link in links:
        src = link['source']
        tgt = link['target']
        if src not in edges:
            edges[src] = []
        edges[src].append(tgt)

    # Run BFS from PER_0001
    reachable = bfs_filter(['PER_0001'], edges, max_depth=3)

    print(f"✓ BFS filtering ejecutado")
    print(f"  Nodos alcanzables desde PER_0001: {len(reachable)}")
    print(f"  Nodos totales: {len(nodes)}")
    print(f"  Loss: {len(nodes) - len(reachable)} nodos no alcanzables")

    # Check specific nodes
    print(f"\n  Nodos clave reachability:")
    for key in ['PER_0001', 'LOC_0013', 'LOC_0014', 'LOC_0064', 'COM_0011']:
        status = "✓" if key in reachable else "❌"
        print(f"    {status} {key}")

    # Check concepts (should not be reachable)
    concept_nodes = [n for n in nodes if n['type'] == 'Concept']
    concepts_reachable = [c for c in concept_nodes if c['id'] in reachable]
    print(f"\n  Conceptos (should be mostly unreachable):")
    print(f"    Total conceptos: {len(concept_nodes)}")
    print(f"    Conceptos alcanzables: {len(concepts_reachable)}")

    print("\n[RESULTADO] Reachability validation:")
    if len(reachable) > 200 and 'LOC_0013' in reachable and 'LOC_0014' in reachable:
        print("✅ PASS - BFS filtering correcto, nodos clave alcanzables")
    else:
        print(f"⚠️  WARN - Reachability issues detected")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("RESUMEN - FASE 2 AUDIT")
print("=" * 80)
print(f"✓ Tareas ejecutadas: 2.1.1 - 2.1.4")
print(f"  - Task 2.1.1: Ingestion validation")
print(f"  - Task 2.1.2: Transformation validation")
print(f"  - Task 2.1.3: Implicit links validation")
print(f"  - Task 2.1.4: Reachability filtering")
print(f"\n⚠️  HALLAZGO CRÍTICO:")
print(f"  parent_org_id en Excel contiene 'Chile', 'Argentina', etc.")
print(f"  No coinciden con ORG_XXXX, por lo que org_to_locations mapping falla")
print(f"  → Implicit event→location links NO se generan correctamente")
print(f"\nPróximos pasos:")
print(f"  1. Verificar si esto es intencional o data error")
print(f"  2. Si es error, actualizar Excel parent_org_id con ORG IDs reales")
print(f"  3. O implementar fallback en ETL (ORG lookup by city/country)")
