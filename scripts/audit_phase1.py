#!/usr/bin/env python3
"""
FASE 1: AUDITORÍA DE DATOS - Excel Master Validation
Tarea 1.1.1 a 1.1.7
"""

import openpyxl
import json
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

EXCEL_PATH = Path('data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx')
EXPECTED_SHEETS = {
    'Agentes_y_Artistas': ['id_agente', 'nombre', 'rol', 'orcid'],
    'Organizaciones': ['id_organizacion', 'nombre', 'tipo'],
    'Lugares_y_Sedes': ['id_lugar', 'nombre', 'ciudad', 'pais', 'coordenadas'],
    'Formacion_Academica': ['id_educacion', 'id_agente', 'id_organizacion', 'titulo', 'año'],
    'Trayectoria_Laboral': ['id_posicion', 'id_agente', 'id_organizacion', 'cargo', 'fecha_inicio'],
    'Publicaciones': ['id_publicacion', 'id_agente', 'titulo', 'año'],
    'Exposiciones_Curadurias': ['id_exposicion', 'id_agente', 'id_organizacion_sede', 'titulo'],
    'Proyectos_y_Fondos': ['id_proyecto', 'id_agente', 'id_organizacion_financiera', 'titulo'],
    'Medios_y_Congresos': ['id_medio', 'id_agente', 'id_organizacion_medio', 'titulo'],
    'Portafolio_Digital_Web': ['id_portafolio', 'id_agente', 'titulo', 'url'],
    'Tesauro_SKOS': ['id_concepto', 'termino_preferente'],
    'Relaciones_Grafo_LOD': ['id_relacion', 'id_origen', 'id_destino', 'predicado']
}

# Regex patterns
ID_PATTERN = re.compile(r'^[A-Z]+_\d+')
ORCID_PATTERN = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$')
QID_PATTERN = re.compile(r'^Q\d+$')
COORD_PATTERN = re.compile(r'^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$')

print("=" * 80)
print("FASE 1: AUDITORÍA DE DATOS - Excel Master")
print("=" * 80)

# Task 1.1.1: Schema Validation
print("\n[TAREA 1.1.1] Validación de Esquema")
print("-" * 80)

try:
    wb = openpyxl.load_workbook(EXCEL_PATH)
    schema_issues = []

    print(f"✓ Excel abierto: {len(wb.sheetnames)} hojas")
    print(f"  Hojas presentes: {', '.join(wb.sheetnames)}\n")

    # Check for missing sheets
    for expected_sheet in EXPECTED_SHEETS:
        if expected_sheet not in wb.sheetnames:
            schema_issues.append(f"❌ HOJA FALTANTE: {expected_sheet}")

    # Check each sheet
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        if sheet.max_row <= 0:
            schema_issues.append(f"⚠️  {sheet_name}: Vacio")
            continue

        # Get headers
        headers = []
        for col in range(1, sheet.max_column + 1):
            cell_val = sheet.cell(1, col).value
            if cell_val:
                headers.append(str(cell_val).strip())

        data_rows = sheet.max_row - 1  # Exclude header
        print(f"  {sheet_name}:")
        print(f"    Filas: {data_rows} | Columnas: {len(headers)}")
        print(f"    Headers: {headers[:3]}..." if len(headers) > 3 else f"    Headers: {headers}")

        # Validate headers if expected
        if sheet_name in EXPECTED_SHEETS:
            expected = EXPECTED_SHEETS[sheet_name]
            for exp_header in expected:
                if not any(h.lower().replace('_', ' ') == exp_header.lower().replace('_', ' ')
                          for h in headers):
                    schema_issues.append(f"⚠️  {sheet_name}: Header '{exp_header}' no encontrado")

        print()

    # Check for duplicate or hidden sheets
    if len(wb.sheetnames) != len(set(wb.sheetnames)):
        schema_issues.append("❌ HOJAS DUPLICADAS DETECTADAS")

    print(f"\n[RESULTADO] Schema validation:")
    if not schema_issues:
        print("✅ PASS - Esquema válido")
    else:
        print("⚠️  ISSUES ENCONTRADOS:")
        for issue in schema_issues:
            print(f"  {issue}")

except Exception as e:
    print(f"❌ ERROR al leer Excel: {e}")
    sys.exit(1)

# Task 1.1.2: Referential Integrity
print("\n[TAREA 1.1.2] Validación de Integridad Referencial")
print("-" * 80)

integrity_issues = []

try:
    # Load all data
    agents_sheet = wb['Agentes_y_Artistas']
    edu_sheet = wb['Formacion_Academica']
    pos_sheet = wb['Trayectoria_Laboral']
    org_sheet = wb['Organizaciones']
    loc_sheet = wb['Lugares_y_Sedes']
    exp_sheet = wb['Exposiciones_Curadurias']
    prj_sheet = wb['Proyectos_y_Fondos']
    com_sheet = wb['Medios_y_Congresos']

    # Extract IDs
    def get_column_data(sheet, col_name, start_row=2):
        col_idx = None
        for col in range(1, sheet.max_column + 1):
            if sheet.cell(1, col).value and str(sheet.cell(1, col).value).strip().lower() == col_name.lower():
                col_idx = col
                break

        if col_idx is None:
            return []

        data = []
        for row in range(start_row, sheet.max_row + 1):
            val = sheet.cell(row, col_idx).value
            if val:
                data.append(str(val).strip())
        return data

    agent_ids = set(get_column_data(agents_sheet, 'id_agente'))
    org_ids = set(get_column_data(org_sheet, 'id_organizacion'))
    loc_ids = set(get_column_data(loc_sheet, 'id_lugar'))

    print(f"✓ Agentes: {len(agent_ids)} | Organizaciones: {len(org_ids)} | Ubicaciones: {len(loc_ids)}")

    # Check Education FKs
    edu_agents = set(get_column_data(edu_sheet, 'id_agente'))
    edu_orgs = set(get_column_data(edu_sheet, 'id_organizacion'))
    missing_edu_agents = edu_agents - agent_ids
    missing_edu_orgs = edu_orgs - org_ids

    if missing_edu_agents:
        integrity_issues.append(f"❌ EDUCACIÓN: {len(missing_edu_agents)} agentes no existen: {missing_edu_agents}")
    if missing_edu_orgs:
        integrity_issues.append(f"⚠️  EDUCACIÓN: {len(missing_edu_orgs)} orgs no existen: {missing_edu_orgs}")
    else:
        print("✓ Educación: FKs válidos")

    # Check Position FKs
    pos_agents = set(get_column_data(pos_sheet, 'id_agente'))
    pos_orgs = set(get_column_data(pos_sheet, 'id_organizacion'))
    missing_pos_agents = pos_agents - agent_ids
    missing_pos_orgs = pos_orgs - org_ids

    if missing_pos_agents:
        integrity_issues.append(f"❌ POSICIONES: {len(missing_pos_agents)} agentes no existen")
    if missing_pos_orgs:
        integrity_issues.append(f"⚠️  POSICIONES: {len(missing_pos_orgs)} orgs no existen")
    else:
        print("✓ Posiciones: FKs válidos")

    # Check Exhibition FKs
    exp_agents = set(get_column_data(exp_sheet, 'id_agente'))
    exp_orgs = set(get_column_data(exp_sheet, 'id_organizacion_sede'))
    missing_exp_agents = exp_agents - agent_ids
    missing_exp_orgs = exp_orgs - org_ids

    if missing_exp_agents:
        integrity_issues.append(f"❌ EXPOSICIONES: {len(missing_exp_agents)} agentes no existen")
    if missing_exp_orgs:
        integrity_issues.append(f"⚠️  EXPOSICIONES: {len(missing_exp_orgs)} orgs no existen")
    else:
        print("✓ Exposiciones: FKs válidos")

    # Check Project FKs
    prj_agents = set(get_column_data(prj_sheet, 'id_agente'))
    prj_orgs = set(get_column_data(prj_sheet, 'id_organizacion_financiera'))
    missing_prj_agents = prj_agents - agent_ids
    missing_prj_orgs = prj_orgs - org_ids

    if missing_prj_agents:
        integrity_issues.append(f"❌ PROYECTOS: {len(missing_prj_agents)} agentes no existen")
    if missing_prj_orgs:
        integrity_issues.append(f"⚠️  PROYECTOS: {len(missing_prj_orgs)} orgs no existen")
    else:
        print("✓ Proyectos: FKs válidos")

    # Check Media FKs
    com_agents = set(get_column_data(com_sheet, 'id_agente'))
    com_orgs = set(get_column_data(com_sheet, 'id_organizacion_medio'))
    missing_com_agents = com_agents - agent_ids
    missing_com_orgs = com_orgs - org_ids

    if missing_com_agents:
        integrity_issues.append(f"❌ MEDIOS: {len(missing_com_agents)} agentes no existen")
    if missing_com_orgs:
        integrity_issues.append(f"⚠️  MEDIOS: {len(missing_com_orgs)} orgs no existen")
    else:
        print("✓ Medios: FKs válidos")

    # Check Location parent_org_id
    loc_parent_orgs = set(get_column_data(loc_sheet, 'parent_org_id'))
    loc_parent_orgs.discard('')  # Remove empty
    loc_parent_orgs.discard('None')
    loc_parent_orgs.discard(None)
    missing_loc_orgs = loc_parent_orgs - org_ids

    if missing_loc_orgs:
        integrity_issues.append(f"⚠️  UBICACIONES: {len(missing_loc_orgs)} parent_org_ids no existen: {missing_loc_orgs}")
    else:
        print("✓ Ubicaciones: parent_org_ids válidos")

    print(f"\n[RESULTADO] Integridad referencial:")
    if not integrity_issues:
        print("✅ PASS - Todas las FKs válidas")
    else:
        for issue in integrity_issues:
            print(f"  {issue}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Task 1.1.3: Locations Audit
print("\n[TAREA 1.1.3] Auditoría de Ubicaciones")
print("-" * 80)

location_issues = []

try:
    loc_sheet = wb['Lugares_y_Sedes']
    locs_data = []

    for row in range(2, loc_sheet.max_row + 1):
        loc_id = loc_sheet.cell(row, 1).value
        if not loc_id:
            continue
        loc_id = str(loc_id).strip()

        loc_info = {
            'id': loc_id,
            'nombre': (loc_sheet.cell(row, 2).value or '').strip(),
            'ciudad': (loc_sheet.cell(row, 3).value or '').strip(),
            'pais': (loc_sheet.cell(row, 4).value or '').strip(),
            'coordenadas': (loc_sheet.cell(row, 5).value or '').strip(),
            'parent_org_id': (loc_sheet.cell(row, 6).value or '').strip() if loc_sheet.max_column >= 6 else '',
        }
        locs_data.append(loc_info)

    print(f"✓ Total ubicaciones: {len(locs_data)}")

    # Validate each location
    coords_valid_count = 0
    coords_invalid = []

    for loc in locs_data:
        # Check label not empty
        if not loc['nombre']:
            location_issues.append(f"❌ {loc['id']}: label vacío")

        # Check coordinates
        if loc['coordenadas'] and loc['coordenadas'].upper() != '[N/A]':
            try:
                parts = loc['coordenadas'].replace('[', '').replace(']', '').split(',')
                if len(parts) == 2:
                    lat, lon = float(parts[0].strip()), float(parts[1].strip())
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        coords_valid_count += 1
                    else:
                        coords_invalid.append(f"{loc['id']}: Coordenadas fuera de rango ({lat}, {lon})")
                else:
                    coords_invalid.append(f"{loc['id']}: Formato inválido: {loc['coordenadas']}")
            except ValueError as e:
                coords_invalid.append(f"{loc['id']}: Parse error: {loc['coordenadas']}")

        # Check parent_org_id
        if loc['parent_org_id'] and loc['parent_org_id'] not in org_ids:
            location_issues.append(f"⚠️  {loc['id']}: parent_org_id '{loc['parent_org_id']}' no existe")

    print(f"✓ Coordenadas válidas: {coords_valid_count}/{len([l for l in locs_data if l['coordenadas']])}")
    if coords_invalid:
        for inv in coords_invalid[:5]:
            location_issues.append(f"⚠️  {inv}")

    # Specific Buenos Aires locations
    print("\n  Buenos Aires locations:")
    for loc in locs_data:
        if loc['ciudad'].lower() == 'buenos aires' or 'buenos aires' in loc['nombre'].lower():
            print(f"    {loc['id']}: {loc['nombre']} - Coords: {loc['coordenadas']}, Parent: {loc['parent_org_id']}")

    print(f"\n[RESULTADO] Auditoría de ubicaciones:")
    if not location_issues:
        print("✅ PASS - Ubicaciones válidas")
    else:
        print("⚠️  ISSUES:")
        for issue in location_issues[:10]:
            print(f"  {issue}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Task 1.1.4: Projects Audit
print("\n[TAREA 1.1.4] Auditoría de Proyectos")
print("-" * 80)

project_issues = []

try:
    prj_sheet = wb['Proyectos_y_Fondos']
    prjs_data = []

    for row in range(2, prj_sheet.max_row + 1):
        prj_id = prj_sheet.cell(row, 1).value
        if not prj_id:
            continue
        prj_id = str(prj_id).strip()

        prj_info = {
            'id': prj_id,
            'id_agente': (prj_sheet.cell(row, 2).value or '').strip(),
            'org_id': (prj_sheet.cell(row, 3).value or '').strip(),
            'titulo': (prj_sheet.cell(row, 4).value or '').strip(),
            'nodo_origen': (prj_sheet.cell(row, 5).value or '').strip() if prj_sheet.max_column >= 5 else '',
            'nodo_destino': (prj_sheet.cell(row, 6).value or '').strip() if prj_sheet.max_column >= 6 else '',
            'coordenadas_origen': (prj_sheet.cell(row, 7).value or '').strip() if prj_sheet.max_column >= 7 else '',
            'coordenadas_destino': (prj_sheet.cell(row, 8).value or '').strip() if prj_sheet.max_column >= 8 else '',
        }
        prjs_data.append(prj_info)

    print(f"✓ Total proyectos: {len(prjs_data)}")

    # Validate
    for prj in prjs_data:
        # Check org exists
        if prj['org_id'] and prj['org_id'] not in org_ids:
            project_issues.append(f"⚠️  {prj['id']}: org_id '{prj['org_id']}' no existe")

        # Check coordinates format
        for coord_type in ['coordenadas_origen', 'coordenadas_destino']:
            coords = prj.get(coord_type, '')
            if coords and coords.upper() != '[N/A]':
                try:
                    parts = coords.replace('[', '').replace(']', '').split(',')
                    if len(parts) == 2:
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            project_issues.append(f"⚠️  {prj['id']}: {coord_type} fuera de rango")
                except ValueError:
                    project_issues.append(f"⚠️  {prj['id']}: {coord_type} parse error")

    # Specific PRJ checks
    print("\n  Proyectos específicos:")
    for prj in prjs_data:
        if prj['id'] in ['PRJ_0005', 'PRJ_0006', 'PRJ_0007']:
            print(f"    {prj['id']}: org={prj['org_id']}, destino={prj['nodo_destino']}")

    print(f"\n[RESULTADO] Auditoría de proyectos:")
    if not project_issues:
        print("✅ PASS - Proyectos válidos")
    else:
        print("⚠️  ISSUES:")
        for issue in project_issues[:10]:
            print(f"  {issue}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Task 1.1.5: Media/Congress Audit
print("\n[TAREA 1.1.5] Auditoría de Medios/Congresos")
print("-" * 80)

media_issues = []

try:
    com_sheet = wb['Medios_y_Congresos']
    coms_data = []

    for row in range(2, com_sheet.max_row + 1):
        com_id = com_sheet.cell(row, 1).value
        if not com_id:
            continue
        com_id = str(com_id).strip()

        com_info = {
            'id': com_id,
            'id_agente': (com_sheet.cell(row, 2).value or '').strip(),
            'org_id': (com_sheet.cell(row, 3).value or '').strip(),
            'titulo': (com_sheet.cell(row, 4).value or '').strip(),
            'nodo_origen': (com_sheet.cell(row, 5).value or '').strip() if com_sheet.max_column >= 5 else '',
            'id_lugar_origen': (com_sheet.cell(row, 6).value or '').strip() if com_sheet.max_column >= 6 else '',
        }
        coms_data.append(com_info)

    print(f"✓ Total medios/congresos: {len(coms_data)}")

    # Check all have PER_0001
    non_jaime = [c for c in coms_data if c['id_agente'] != 'PER_0001']
    if non_jaime:
        media_issues.append(f"⚠️  {len(non_jaime)} medios con id_agente ≠ PER_0001")
    else:
        print("✓ Todos los medios tienen id_agente = PER_0001")

    # Check orgs exist
    missing_orgs = [c['org_id'] for c in coms_data if c['org_id'] and c['org_id'] not in org_ids]
    if missing_orgs:
        media_issues.append(f"⚠️  {len(set(missing_orgs))} orgs no existen: {set(missing_orgs)}")
    else:
        print("✓ Todos los org_ids válidos")

    # Check locations
    with_loc = [c for c in coms_data if c['id_lugar_origen']]
    without_loc = [c for c in coms_data if not c['id_lugar_origen']]
    print(f"✓ Medios con id_lugar_origen: {len(with_loc)}/{len(coms_data)}")

    if without_loc and len(without_loc) <= 5:
        for c in without_loc:
            print(f"  ⚠️  {c['id']}: Sin id_lugar_origen (depende de org_to_locations)")

    # Specific COM_0011 check
    com_0011 = next((c for c in coms_data if c['id'] == 'COM_0011'), None)
    if com_0011:
        print(f"\n  COM_0011 específicamente:")
        print(f"    org_id: {com_0011['org_id']}")
        print(f"    nodo_origen: {com_0011['nodo_origen']}")
        print(f"    id_lugar_origen: {com_0011['id_lugar_origen']}")

    print(f"\n[RESULTADO] Auditoría de medios/congresos:")
    if not media_issues:
        print("✅ PASS - Medios válidos")
    else:
        print("⚠️  ISSUES:")
        for issue in media_issues:
            print(f"  {issue}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("RESUMEN FASE 1")
print("=" * 80)
print(f"✓ Tareas ejecutadas: 1.1.1 - 1.1.5")
print(f"  - Task 1.1.1: Schema validation")
print(f"  - Task 1.1.2: Referential integrity")
print(f"  - Task 1.1.3: Locations audit")
print(f"  - Task 1.1.4: Projects audit")
print(f"  - Task 1.1.5: Media/Congress audit")
print(f"\nPróximas tareas: 1.1.6 (Relaciones), 1.1.7 (Agentes)")
