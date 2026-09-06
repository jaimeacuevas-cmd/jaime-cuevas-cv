#!/usr/bin/env python3
"""
FASE 6: AUDITORÍA DE REPRODUCIBILIDAD
Validación de build idempotence: ejecutar 2 veces, verificar outputs idénticos
"""

import json
import subprocess
import hashlib
import time
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("FASE 6: AUDITORÍA DE REPRODUCIBILIDAD (BUILD IDEMPOTENCE)")
print("=" * 80)

# Task 6.1: Clean and prepare for first build
print("\n[TAREA 6.1] Preparación: Limpiar dist/ anterior")
print("-" * 80)

try:
    dist_path = Path('dist/data')
    if dist_path.exists():
        graph_file = dist_path / 'graph_data.json'
        geo_file = dist_path / 'cartografia.geojson'
        ttl_file = dist_path / 'jaime_knowledge_graph.ttl'

        # Backup existing files for comparison
        backup_files = {}
        for f in [graph_file, geo_file, ttl_file]:
            if f.exists():
                backup_files[f.name] = f.read_text(encoding='utf-8', errors='ignore')

        print(f"✓ Guardadas versiones anteriores de {len(backup_files)} archivos")

except Exception as e:
    print(f"❌ ERROR: {e}")

# Task 6.2: First build execution
print("\n[TAREA 6.2] Ejecución BUILD #1")
print("-" * 80)

start_time_build1 = time.time()
result_build1 = subprocess.run(['python3', 'scripts/build.py'], capture_output=True, text=True)
elapsed_build1 = time.time() - start_time_build1

print(f"Build #1 exitoso: {'✓' if result_build1.returncode == 0 else '❌'}")
print(f"Tiempo: {elapsed_build1:.2f}s")
if result_build1.returncode != 0:
    print(f"STDERR: {result_build1.stderr[:500]}")

# Capture outputs from first build
build1_outputs = {}
print("\nArchivos generados en BUILD #1:")

for file_path, name in [
    (dist_path / 'graph_data.json', 'graph_data.json'),
    (dist_path / 'cartografia.geojson', 'cartografia.geojson'),
    (dist_path / 'jaime_knowledge_graph.ttl', 'jaime_knowledge_graph.ttl'),
]:
    if file_path.exists():
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        size = len(content)
        checksum = hashlib.sha256(content.encode()).hexdigest()
        line_count = len(content.split('\n'))
        build1_outputs[name] = {
            'size': size,
            'checksum': checksum,
            'lines': line_count,
            'content': content
        }
        print(f"  ✓ {name}: {size} bytes, {line_count} lines")
        print(f"    SHA256: {checksum}")
    else:
        print(f"  ❌ {name}: NO ENCONTRADO")

# Task 6.3: Second build execution
print("\n[TAREA 6.3] Ejecución BUILD #2")
print("-" * 80)

start_time_build2 = time.time()
result_build2 = subprocess.run(['python3', 'scripts/build.py'], capture_output=True, text=True)
elapsed_build2 = time.time() - start_time_build2

print(f"Build #2 exitoso: {'✓' if result_build2.returncode == 0 else '❌'}")
print(f"Tiempo: {elapsed_build2:.2f}s")
if result_build2.returncode != 0:
    print(f"STDERR: {result_build2.stderr[:500]}")

# Capture outputs from second build
build2_outputs = {}
print("\nArchivos generados en BUILD #2:")

for file_path, name in [
    (dist_path / 'graph_data.json', 'graph_data.json'),
    (dist_path / 'cartografia.geojson', 'cartografia.geojson'),
    (dist_path / 'jaime_knowledge_graph.ttl', 'jaime_knowledge_graph.ttl'),
]:
    if file_path.exists():
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        size = len(content)
        checksum = hashlib.sha256(content.encode()).hexdigest()
        line_count = len(content.split('\n'))
        build2_outputs[name] = {
            'size': size,
            'checksum': checksum,
            'lines': line_count,
            'content': content
        }
        print(f"  ✓ {name}: {size} bytes, {line_count} lines")
        print(f"    SHA256: {checksum}")
    else:
        print(f"  ❌ {name}: NO ENCONTRADO")

# Task 6.4: Compare outputs
print("\n[TAREA 6.4] Comparación: BUILD #1 vs BUILD #2")
print("-" * 80)

idempotent = True
comparison_results = {}

for filename in build1_outputs.keys():
    b1 = build1_outputs[filename]
    b2 = build2_outputs.get(filename)

    if not b2:
        print(f"❌ {filename}: NO PRESENTE EN BUILD #2")
        idempotent = False
        comparison_results[filename] = 'MISSING_IN_BUILD2'
        continue

    # Compare sizes
    size_match = b1['size'] == b2['size']

    # Compare checksums
    checksum_match = b1['checksum'] == b2['checksum']

    # Compare line counts
    lines_match = b1['lines'] == b2['lines']

    status = '✓' if (size_match and checksum_match) else '❌'
    print(f"\n{status} {filename}:")
    print(f"  Size:     {b1['size']:>10} bytes | {b2['size']:>10} bytes | {'✓' if size_match else '❌ MISMATCH'}")
    print(f"  Lines:    {b1['lines']:>10} lines  | {b2['lines']:>10} lines  | {'✓' if lines_match else '❌ MISMATCH'}")
    print(f"  SHA256:   {b1['checksum'][:16]}... | {b2['checksum'][:16]}...")

    if checksum_match:
        print(f"  ✓ BYTE-FOR-BYTE IDENTICAL")
        comparison_results[filename] = 'IDENTICAL'
    else:
        print(f"  ❌ CHECKSUM MISMATCH - Outputs differ!")
        comparison_results[filename] = 'DIFFERENT'
        idempotent = False

        # Analyze differences
        if filename.endswith('.json'):
            try:
                j1 = json.loads(b1['content'])
                j2 = json.loads(b2['content'])

                # Check node/link counts
                if isinstance(j1, dict):
                    nodes1 = len(j1.get('nodes', []))
                    nodes2 = len(j2.get('nodes', []))
                    links1 = len(j1.get('links', []))
                    links2 = len(j2.get('links', []))

                    print(f"    Nodes: {nodes1} vs {nodes2}")
                    print(f"    Links: {links1} vs {links2}")

                # Find first difference
                lines1 = b1['content'].split('\n')
                lines2 = b2['content'].split('\n')
                for i, (l1, l2) in enumerate(zip(lines1, lines2)):
                    if l1 != l2:
                        print(f"    First diff at line {i+1}:")
                        print(f"      Build1: {l1[:80]}")
                        print(f"      Build2: {l2[:80]}")
                        break
            except:
                pass

print(f"\n[RESULTADO] Idempotencia: {'✅ PASS' if idempotent else '❌ FAIL'}")

# Task 6.5: Check for spurious files
print("\n[TAREA 6.5] Validación de archivos generados")
print("-" * 80)

expected_files = {
    'dist/data/graph_data.json',
    'dist/data/cartografia.geojson',
    'dist/data/jaime_knowledge_graph.ttl',
}

all_files_present = True
for filename in expected_files:
    path = Path(filename)
    exists = path.exists()
    status = '✓' if exists else '❌'
    print(f"{status} {filename}")
    if not exists:
        all_files_present = False

print(f"\n[RESULTADO] Archivo completeness: {'✅ PASS' if all_files_present else '❌ FAIL'}")

# Task 6.6: Performance check
print("\n[TAREA 6.6] Análisis de rendimiento")
print("-" * 80)

print(f"Build #1 tiempo: {elapsed_build1:.2f}s")
print(f"Build #2 tiempo: {elapsed_build2:.2f}s")
print(f"Diferencia:      {abs(elapsed_build1 - elapsed_build2):.2f}s ({abs(elapsed_build1 - elapsed_build2)/max(elapsed_build1, elapsed_build2)*100:.1f}%)")

perf_acceptable = abs(elapsed_build1 - elapsed_build2) < 5 and max(elapsed_build1, elapsed_build2) < 30
print(f"\n[RESULTADO] Performance acceptable: {'✅ PASS' if perf_acceptable else '⚠️ CHECK'}")

# Summary
print("\n" + "=" * 80)
print("RESUMEN FASE 6 - AUDITORÍA DE REPRODUCIBILIDAD")
print("=" * 80)

print("\nComparación de builds:")
for filename, result in comparison_results.items():
    status = '✅' if result == 'IDENTICAL' else '❌'
    print(f"  {status} {filename}: {result}")

print(f"\nMétricas globales:")
print(f"  Builds exitosos:    {'✅ 2/2' if result_build1.returncode == 0 and result_build2.returncode == 0 else '❌ FAILED'}")
print(f"  Outputs idénticos:  {'✅ YES' if idempotent else '❌ NO'}")
print(f"  Archivos completos: {'✅ YES' if all_files_present else '❌ NO'}")
print(f"  Performance OK:     {'✅ YES' if perf_acceptable else '⚠️ CHECK'}")

print(f"\n{'✅ FASE 6 BUILD REPRODUCIBILITY PASS' if idempotent and all_files_present else '⚠️ FASE 6 CHECK REQUIRED'}")
print(f"   Próximos pasos: Validación final de SEGURIDAD & RENDIMIENTO (Fase 7)")
