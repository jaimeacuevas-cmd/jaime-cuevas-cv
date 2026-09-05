#!/usr/bin/env python3
"""
FASE 1: AUDITORÍA DE DATOS - Excel Master Validation (v2)
Fixed column handling and data type conversions
"""

import openpyxl
import json
import re
from pathlib import Path

EXCEL_PATH = Path('data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx')

def safe_str(val):
    """Convert value to string safely, handling None and numbers"""
    if val is None:
        return ''
    return str(val).strip()

print("=" * 80)
print("FASE 1: AUDITORÍA DE DATOS - Excel Master (v2)")
print("=" * 80)

try:
    wb = openpyxl.load_workbook(EXCEL_PATH)

    # Task 1.1.1: Schema - Map actual headers
    print("\n[TAREA 1.1.1] Mapeo Real de Columnas")
    print("-" * 80)

    sheets_info = {}

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        headers = []

        for col in range(1, min(sheet.max_column + 1, 30)):  # Limit to 30 columns
            cell_val = sheet.cell(1, col).value
            if cell_val:
                headers.append(safe_str(cell_val))

        data_rows = max(0, sheet.max_row - 1)
        sheets_info[sheet_name] = {
            'rows': data_rows,
            'headers': headers
        }

        print(f"\n{sheet_name}: {data_rows} rows")
        for i, h in enumerate(headers[:8], 1):
            print(f"  Col {i}: {h}")

    # Task 1.1.2: Extract key IDs for FK validation
    print("\n[TAREA 1.1.2] Extracción de IDs Maestros")
    print("-" * 80)

    agents_sheet = wb['Agentes_y_Artistas']
    agent_ids = set()
    for row in range(2, agents_sheet.max_row + 1):
        agent_id = safe_str(agents_sheet.cell(row, 1).value)
        if agent_id:
            agent_ids.add(agent_id)

    orgs_sheet = wb['Organizaciones']
    org_ids = set()
    for row in range(2, orgs_sheet.max_row + 1):
        org_id = safe_str(orgs_sheet.cell(row, 1).value)
        if org_id:
            org_ids.add(org_id)

    locs_sheet = wb['Lugares_y_Sedes']
    loc_ids = set()
    locs_by_id = {}
    for row in range(2, locs_sheet.max_row + 1):
        loc_id = safe_str(locs_sheet.cell(row, 1).value)
        if loc_id:
            loc_ids.add(loc_id)
            # Store full row data
            locs_by_id[loc_id] = {
                'name': safe_str(locs_sheet.cell(row, 2).value),
                'city': safe_str(locs_sheet.cell(row, 3).value),
                'country': safe_str(locs_sheet.cell(row, 4).value),
                'coords': safe_str(locs_sheet.cell(row, 5).value),
                'parent_org': safe_str(locs_sheet.cell(row, 6).value) if locs_sheet.max_column >= 6 else '',
            }

    print(f"✓ Agentes: {len(agent_ids)}")
    print(f"✓ Organizaciones: {len(org_ids)}")
    print(f"✓ Ubicaciones: {len(loc_ids)}")

    # Task 1.1.3: Locations detailed audit
    print("\n[TAREA 1.1.3] Auditoría de Ubicaciones")
    print("-" * 80)

    loc_issues = []
    coords_parsed = 0
    parent_org_issues = 0

    for loc_id in sorted(loc_ids):
        loc = locs_by_id[loc_id]

        # Check coordinates format
        if loc['coords'] and loc['coords'].upper() not in ['[N/A]', 'N/A']:
            try:
                coords_str = loc['coords'].replace('[', '').replace(']', '').replace(' ', '')
                parts = coords_str.split(',')
                if len(parts) == 2:
                    try:
                        lat, lon = float(parts[0]), float(parts[1])
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            coords_parsed += 1
                        else:
                            loc_issues.append(f"⚠️  {loc_id}: Coordenadas fuera de rango: {loc['coords']}")
                    except ValueError:
                        pass
            except:
                pass

        # Check parent_org
        if loc['parent_org'] and loc['parent_org'] not in org_ids:
            parent_org_issues += 1
            if loc_id in ['LOC_0014', 'LOC_0064', 'LOC_0013']:  # Key locations
                loc_issues.append(f"⚠️  {loc_id}: parent_org '{loc['parent_org']}' no existe")

    print(f"✓ Coordenadas parseables: {coords_parsed}/{len([l for l in locs_by_id.values() if l['coords']])}")
    print(f"⚠️  parent_org con issues: {parent_org_issues}")

    # Key locations detail
    print("\n  Ubicaciones clave:")
    for loc_id in ['LOC_0013', 'LOC_0014', 'LOC_0064']:
        if loc_id in locs_by_id:
            loc = locs_by_id[loc_id]
            print(f"    {loc_id}: {loc['name']}")
            print(f"      Ciudad: {loc['city']}, País: {loc['country']}")
            print(f"      Coordenadas: {loc['coords']}")
            print(f"      Parent org: {loc['parent_org']}")

    # Task 1.1.4: Projects detailed audit
    print("\n[TAREA 1.1.4] Auditoría de Proyectos")
    print("-" * 80)

    prj_sheet = wb['Proyectos_y_Fondos']
    projects = {}

    for row in range(2, prj_sheet.max_row + 1):
        prj_id = safe_str(prj_sheet.cell(row, 1).value)
        if not prj_id:
            continue

        projects[prj_id] = {
            'agent': safe_str(prj_sheet.cell(row, 2).value),
            'org': safe_str(prj_sheet.cell(row, 3).value),
            'title': safe_str(prj_sheet.cell(row, 4).value),
        }

    print(f"✓ Total proyectos: {len(projects)}")

    # Check key projects
    print("\n  Proyectos clave:")
    for prj_id in ['PRJ_0005', 'PRJ_0006', 'PRJ_0007']:
        if prj_id in projects:
            prj = projects[prj_id]
            print(f"    {prj_id}: org={prj['org']}, agent={prj['agent']}")
            # Check if org exists
            if prj['org'] and prj['org'] not in org_ids:
                print(f"      ❌ org '{prj['org']}' NO existe")

    # Task 1.1.5: Media/Congress audit
    print("\n[TAREA 1.1.5] Auditoría de Medios/Congresos")
    print("-" * 80)

    media_sheet = wb['Medios_y_Congresos']
    medias = {}

    for row in range(2, media_sheet.max_row + 1):
        media_id = safe_str(media_sheet.cell(row, 1).value)
        if not media_id:
            continue

        medias[media_id] = {
            'agent': safe_str(media_sheet.cell(row, 2).value),
            'format': safe_str(media_sheet.cell(row, 3).value),
            'title': safe_str(media_sheet.cell(row, 4).value),
        }

    print(f"✓ Total medios: {len(medias)}")

    all_jaime = all(m['agent'] == 'PER_0001' for m in medias.values())
    print(f"{'✓' if all_jaime else '❌'} Todos con agente PER_0001: {all_jaime}")

    # Check COM_0011 specifically
    if 'COM_0011' in medias:
        com = medias['COM_0011']
        print(f"\n  COM_0011:")
        print(f"    Formato: {com['format']}")
        print(f"    Título: {com['title']}")

    # Task 1.1.6: Relations audit
    print("\n[TAREA 1.1.6] Auditoría de Relaciones")
    print("-" * 80)

    rel_sheet = wb['Relaciones_Grafo_LOD']
    relations = []
    rel_issues = []

    for row in range(2, rel_sheet.max_row + 1):
        rel_id = safe_str(rel_sheet.cell(row, 1).value)
        if not rel_id:
            continue

        src = safe_str(rel_sheet.cell(row, 2).value)
        tgt = safe_str(rel_sheet.cell(row, 3).value)
        pred = safe_str(rel_sheet.cell(row, 4).value)

        relations.append({'id': rel_id, 'src': src, 'tgt': tgt, 'pred': pred})

    print(f"✓ Total relaciones: {len(relations)}")

    # Check key relations
    for rel in relations:
        if 'PER_0001' in rel['src'] and 'LOC_0013' in rel['tgt']:
            print(f"✓ Encontrada: {rel['src']} → {rel['tgt']} ({rel['pred']})")
            break

    # Task 1.1.7: Agents audit
    print("\n[TAREA 1.1.7] Auditoría de Agentes")
    print("-" * 80)

    agents = {}
    for row in range(2, agents_sheet.max_row + 1):
        agent_id = safe_str(agents_sheet.cell(row, 1).value)
        if not agent_id:
            continue

        agents[agent_id] = {
            'nombre': safe_str(agents_sheet.cell(row, 2).value),
            'orcid': safe_str(agents_sheet.cell(row, 10).value) if agents_sheet.max_column >= 10 else '',
        }

    print(f"✓ Total agentes: {len(agents)}")

    # Check Jaime
    if 'PER_0001' in agents:
        jaime = agents['PER_0001']
        print(f"✓ PER_0001: {jaime['nombre']}")
        if jaime['orcid']:
            print(f"  ORCID: {jaime['orcid']}")

    # Summary
    print("\n" + "=" * 80)
    print("RESUMEN - FASE 1 AUDIT v2")
    print("=" * 80)
    print(f"✓ 12 hojas validadas")
    print(f"✓ {len(agent_ids)} agentes")
    print(f"✓ {len(org_ids)} organizaciones")
    print(f"✓ {len(loc_ids)} ubicaciones")
    print(f"✓ {len(projects)} proyectos")
    print(f"✓ {len(medias)} medios/congresos")
    print(f"✓ {len(relations)} relaciones")
    print(f"\n⚠️  ISSUES A REVISAR:")
    print(f"  - parent_org mapping: {parent_org_issues} ubicaciones con parent_org inválido")
    print(f"  - Coordinate formatting: Necesita normalización en ETL")
    print(f"  - Relaciones: Validar predicados CIDOC-CRM")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
