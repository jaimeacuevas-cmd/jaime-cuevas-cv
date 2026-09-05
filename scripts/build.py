#!/usr/bin/env python3
"""
ETL Pipeline Orchestrator for CV Dataset Consolidation.

Reads: data/CV_Dataset_Maestro_Jaime_Cuevas.xlsx (12 sheets, ~372 rows)
Generates:
  - data/graph_data.json (D3.js visualization data)
  - data/cartografia.geojson (Leaflet map data)
  - data/jaime_knowledge_graph.ttl (RDF/Turtle linked data)
Injects: Data into dist/index.html and copies to dist/data/
"""

import sys
import json
import logging
import os
import shutil
from pathlib import Path
from datetime import datetime

# Setup paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
DIST_DIR = BASE_DIR / 'dist'
DIST_DATA_DIR = DIST_DIR / 'data'

# Add scripts to path
sys.path.insert(0, str(BASE_DIR / 'scripts'))

from etl.ingestion import ExcelReader
from etl.transformation import DataTransformer
from etl.validation import DataValidator
from etl.output_generator import OutputGenerator
from etl.audit_checklist import AuditChecklist

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL pipeline orchestrator."""

    def __init__(self, base_dir: Path):
        """Initialize pipeline with base directory."""
        self.base_dir = base_dir
        self.data_dir = base_dir / 'data'
        self.dist_dir = base_dir / 'dist'
        self.dist_data_dir = self.dist_dir / 'data'

    def run(self) -> bool:
        """
        Execute full ETL pipeline.
        Returns True if successful, False otherwise.
        """
        try:
            logger.info("=" * 70)
            logger.info("Starting ETL Pipeline: Pipeline Fuente Única")
            logger.info("=" * 70)

            # Stage 1: Ingestion
            logger.info("\n[STAGE 1] INGESTION - Reading Excel master file...")
            reader = ExcelReader(self.data_dir / 'CV_Dataset_Maestro_Jaime_Cuevas.xlsx')

            raw_entities = reader.read_all_sheets()
            relations_raw = reader.read_relations()

            if not raw_entities:
                logger.error("No entities found in Excel file!")
                return False

            logger.info(f"✓ Ingestion complete: {sum(len(v) for v in raw_entities.values())} total rows")

            # Stage 2: Transformation
            logger.info("\n[STAGE 2] TRANSFORMATION - Converting 12 sheets to unified model...")
            transformer = DataTransformer()
            nodes, links = transformer.transform(raw_entities, relations_raw)

            if not nodes:
                logger.error("Transformation produced no nodes!")
                return False

            # Save full graph for audit
            nodes_full = list(nodes)
            links_full = list(links)

            logger.info(f"✓ Transformation complete: {len(nodes)} nodes, {len(links)} links")

            # Stage 3: Validation
            logger.info("\n[STAGE 3] VALIDATION - Quality assurance (permissive mode)...")
            validator = DataValidator()
            validation_report = validator.validate(nodes, links)

            if validation_report['warning_count'] > 0:
                logger.warning(f"⚠ {validation_report['warning_count']} validation warnings found")
                for warning in validation_report['warnings'][:5]:
                    logger.warning(f"  - {warning}")

            logger.info(f"✓ Validation complete: {validation_report['checks_run']} checks run")

            # Stage 4: Apply Overrides
            logger.info("\n[STAGE 4] OVERRIDES - Applying curated metadata...")
            nodes = self._apply_overrides(nodes)
            logger.info(f"✓ Overrides applied")

            # Stage 5: Generate Outputs
            logger.info("\n[STAGE 5] OUTPUT GENERATION - Creating artifacts...")
            generator = OutputGenerator()

            graph_data = generator.generate_graph_json(nodes, links, validation_report)
            geo_data = generator.generate_geojson(nodes, links)
            turtle_data = generator.generate_turtle(nodes, links)

            # Create dist directories
            self.dist_dir.mkdir(parents=True, exist_ok=True)
            self.dist_data_dir.mkdir(parents=True, exist_ok=True)

            # Write outputs to data/
            logger.info("\n[STAGE 6] WRITING OUTPUTS...")

            graph_file = self.data_dir / 'graph_data.json'
            geo_file = self.data_dir / 'cartografia.geojson'
            ttl_file = self.data_dir / 'jaime_knowledge_graph.ttl'

            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✓ Written: {graph_file}")

            with open(geo_file, 'w', encoding='utf-8') as f:
                json.dump(geo_data, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✓ Written: {geo_file}")

            with open(ttl_file, 'w', encoding='utf-8') as f:
                f.write(turtle_data)
            logger.info(f"  ✓ Written: {ttl_file}")

            # Copy outputs to dist/data/
            logger.info("\n[STAGE 7] DEPLOYING TO dist/...")

            for filename in ['graph_data.json', 'cartografia.geojson', 'jaime_knowledge_graph.ttl', 'schema_jaime_cuevas.json', 'CV_Dataset_Maestro_Jaime_Cuevas.xlsx']:
                src = self.data_dir / filename
                if src.exists():
                    dst = self.dist_data_dir / filename
                    shutil.copy(src, dst)
                    logger.info(f"  ✓ Copied: {filename}")

            # Inject data into HTML
            logger.info("\n[STAGE 8] INJECTING DATA INTO HTML...")
            self._inject_data_into_html(graph_data, geo_data, turtle_data)
            logger.info(f"  ✓ Injected data into dist/index.html")

            # Stage 9: Audit Checklist
            logger.info("\n[STAGE 9] AUDIT - Validating data integrity...")
            nodes_filtered = graph_data.get('nodes', [])
            links_filtered = graph_data.get('links', [])

            audit = AuditChecklist(nodes_full, links_full, nodes_filtered, links_filtered)
            audit_passed, issues, warnings = audit.run_all_checks()

            if not audit_passed:
                logger.error(f"\n✗ AUDIT FAILED with {len(issues)} critical issues:")
                for issue in issues:
                    logger.error(f"  ✗ {issue}")
                return False

            if warnings:
                logger.warning(f"\n⚠  AUDIT WARNINGS ({len(warnings)}):")
                for warning in warnings[:5]:
                    logger.warning(f"  - {warning}")

            # Final summary
            logger.info("\n" + "=" * 70)
            logger.info("✓ ETL PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"Full Graph: {len(nodes_full)} nodes, {len(links_full)} links")
            logger.info(f"Filtered Graph: {len(nodes_filtered)} nodes, {len(links_filtered)} links")
            logger.info(f"Validation Warnings: {validation_report['warning_count']}")
            logger.info(f"Audit Issues: {len(issues)}, Warnings: {len(warnings)}")
            logger.info(f"Output: {self.dist_dir}/")
            logger.info("=" * 70)

            return True

        except Exception as e:
            logger.error(f"✗ ETL PIPELINE FAILED: {e}", exc_info=True)
            return False

    def _apply_overrides(self, nodes) -> list:
        """
        Apply curated metadata overrides from data/overrides.json.
        Preserves manual curation without losing source data.
        """
        overrides_file = self.data_dir / 'overrides.json'

        if not overrides_file.exists():
            logger.info("  No overrides.json found, skipping")
            return nodes

        try:
            with open(overrides_file, 'r', encoding='utf-8') as f:
                overrides = json.load(f)

            override_fields = {'is_core', 'short_name', 'description', 'category', 'role', 'period', 'url', 'why_relevant', 'micro_summary'}

            for node in nodes:
                node_id = node.get('id')
                if node_id in overrides:
                    override_data = overrides[node_id]
                    for field in override_fields:
                        if field in override_data:
                            node[field] = override_data[field]
                            node[f'_{field}_override'] = True

            logger.info(f"  Applied overrides to {len(overrides)} nodes")
            return nodes

        except Exception as e:
            logger.warning(f"  Error reading overrides: {e}")
            return nodes

    def _inject_data_into_html(self, graph_data, geo_data, turtle_data):
        """
        Inject data into index.html template.
        Creates hybrid bundled + fetch mode.
        """
        html_src = self.base_dir / 'index.html'
        html_dst = self.dist_dir / 'index.html'

        if not html_src.exists():
            logger.warning("  index.html source not found")
            return

        with open(html_src, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Create bundled data injection
        # Escape special characters for JavaScript
        graph_json = json.dumps(graph_data)
        geo_json = json.dumps(geo_data)

        # Escape backticks, backslashes, and ${ for Turtle in template literals
        turtle_escaped = (turtle_data
                          .replace('\\', '\\\\')
                          .replace('`', '\\`')
                          .replace('${', '\\${'))

        injection_script = f"""
  <script>
    // Bundled data for fallback (hybrid mode)
    window.BUNDLED_DATA = {{
      graph: {graph_json},
      geo: {geo_json},
      ttl: `{turtle_escaped}`
    }};
  </script>
"""

        # Find insertion point (before closing body or after first script)
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', injection_script + '</body>')
        elif '<body>' in html_content:
            body_end = html_content.find('<body>') + len('<body>')
            html_content = html_content[:body_end] + injection_script + html_content[body_end:]
        else:
            # Fallback: append before closing html
            html_content = html_content.replace('</html>', injection_script + '</html>')

        # Write injected HTML to dist
        with open(html_dst, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"  Injected bundled data into {html_dst}")


if __name__ == '__main__':
    pipeline = ETLPipeline(BASE_DIR)
    success = pipeline.run()
    sys.exit(0 if success else 1)
