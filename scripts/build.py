import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DIST_DIR = os.path.join(BASE_DIR, 'dist')
DIST_DATA_DIR = os.path.join(DIST_DIR, 'data')

os.makedirs(DIST_DATA_DIR, exist_ok=True)

# Copy data files to dist/data/ for direct download
for fn in ['graph_data.json', 'cartografia.geojson', 'schema_jaime_cuevas.json', 'jaime_knowledge_graph.ttl', 'CV_Dataset_Maestro_Jaime_Cuevas.xlsx']:
    src = os.path.join(DATA_DIR, fn)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(DIST_DATA_DIR, fn))

# Copy main HTML
shutil.copy(os.path.join(BASE_DIR, 'index.html'), os.path.join(DIST_DIR, 'index.html'))
print("Build completed successfully: dist/ ready for deployment.")
