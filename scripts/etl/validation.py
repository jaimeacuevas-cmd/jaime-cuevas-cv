"""Data validation and quality assurance module."""

import logging
import re
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality with CIDOC-CRM and LOD compliance."""

    def __init__(self):
        """Initialize validator with empty report."""
        self.errors = []
        self.warnings = []
        self.checks_run = 0
        self.status = 'PASS'

    def validate(self, nodes: List[Dict], links: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Main validation entry point. Run all checks.
        Returns validation report.
        """
        logger.info("Starting data validation (PERMISSIVE mode)...")

        # Check 1: Node ID format
        self._check_node_ids(nodes)

        # Check 2: Required fields
        self._check_required_fields(nodes)

        # Check 3: ORCID format (for Agents)
        self._check_orcid_format(nodes)

        # Check 4: Wikidata QID format (for Orgs/Locations)
        self._check_wikidata_qids(nodes)

        # Check 5: LOD rules (Agents must not have Wikidata)
        self._check_lod_rules(nodes)

        # Check 6: Coordinates validity (for Locations)
        self._check_coordinates(nodes)

        # Check 7: Link integrity (if provided)
        if links:
            self._check_link_integrity(links, nodes)

        # Check 8: Duplicates
        self._check_duplicates(nodes)

        # Build report
        report = {
            'status': self.status,
            'checks_run': self.checks_run,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors[:10],  # First 10 errors
            'warnings': self.warnings[:20],  # First 20 warnings
            'node_count': len(nodes),
            'link_count': len(links) if links else 0,
            'generated_at': __import__('datetime').datetime.now().isoformat(),
        }

        if self.status == 'PASS':
            logger.info(f"✓ Validation PASSED: {self.checks_run} checks, {len(self.warnings)} warnings")
        else:
            logger.warning(f"⚠ Validation WARNING: {len(self.errors)} errors, {len(self.warnings)} warnings")

        return report

    def _check_node_ids(self, nodes: List[Dict]) -> None:
        """Validate node ID format: TYPE_NNNN"""
        self.checks_run += 1
        pattern = r'^[A-Z]{3}_\d{4}$'

        for node in nodes:
            node_id = node.get('id', '')
            if not re.match(pattern, node_id):
                self.warnings.append(f"Invalid ID format: {node_id} (expected TYPE_NNNN)")

        logger.info(f"  ✓ Checked node ID format")

    def _check_required_fields(self, nodes: List[Dict]) -> None:
        """Check that all nodes have required fields."""
        self.checks_run += 1
        required = ['id', 'type', 'label']

        for node in nodes:
            for field in required:
                if field not in node or not node[field]:
                    self.warnings.append(f"Missing required field '{field}' in node {node.get('id')}")

        logger.info(f"  ✓ Checked required fields")

    def _check_orcid_format(self, nodes: List[Dict]) -> None:
        """Validate ORCID format for Agent nodes."""
        self.checks_run += 1
        pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$'

        for node in nodes:
            if node.get('type') != 'Agent':
                continue

            orcid = node.get('orcid')
            if orcid:
                if not re.match(pattern, str(orcid)):
                    self.warnings.append(
                        f"Invalid ORCID format in {node.get('id')}: {orcid} "
                        f"(expected NNNN-NNNN-NNNN-NNN[0-9X])"
                    )

        logger.info(f"  ✓ Checked ORCID format")

    def _check_wikidata_qids(self, nodes: List[Dict]) -> None:
        """Validate Wikidata QID format for Orgs/Locations."""
        self.checks_run += 1
        pattern = r'^Q\d+$'
        synthetic_range = (124618790, 124618818)

        for node in nodes:
            if node.get('type') not in ['Organization', 'Location']:
                continue

            qid = node.get('wikidata')
            if qid:
                if not re.match(pattern, str(qid)):
                    self.warnings.append(
                        f"Invalid Wikidata QID in {node.get('id')}: {qid} (expected Q followed by digits)"
                    )
                else:
                    # Check for synthetic QIDs
                    qid_num = int(qid[1:])
                    if synthetic_range[0] <= qid_num <= synthetic_range[1]:
                        self.warnings.append(
                            f"Synthetic Wikidata QID detected in {node.get('id')}: {qid} "
                            f"(in synthetic range Q{synthetic_range[0]}-Q{synthetic_range[1]})"
                        )

        logger.info(f"  ✓ Checked Wikidata QID format")

    def _check_lod_rules(self, nodes: List[Dict]) -> None:
        """Validate Linked Open Data rules."""
        self.checks_run += 1

        for node in nodes:
            # Rule: Agents must NOT have Wikidata QID
            if node.get('type') == 'Agent' and node.get('wikidata'):
                self.warnings.append(
                    f"LOD violation: Agent {node.get('id')} has Wikidata QID {node.get('wikidata')} "
                    f"(agents should not have QID)"
                )

        logger.info(f"  ✓ Checked LOD rules")

    def _check_coordinates(self, nodes: List[Dict]) -> None:
        """Validate geographic coordinates for Location nodes."""
        self.checks_run += 1

        for node in nodes:
            if node.get('type') != 'Location':
                continue

            coords = node.get('coordinates')
            if coords:
                try:
                    lon, lat = float(coords[0]), float(coords[1])

                    if not (-180 <= lon <= 180):
                        self.warnings.append(
                            f"Invalid longitude in {node.get('id')}: {lon} (must be -180 to 180)"
                        )

                    if not (-90 <= lat <= 90):
                        self.warnings.append(
                            f"Invalid latitude in {node.get('id')}: {lat} (must be -90 to 90)"
                        )

                except (ValueError, TypeError, IndexError):
                    self.warnings.append(
                        f"Invalid coordinates in {node.get('id')}: {coords}"
                    )

        logger.info(f"  ✓ Checked geographic coordinates")

    def _check_link_integrity(self, links: List[Dict], nodes: List[Dict]) -> None:
        """Validate that all link sources/targets reference existing nodes."""
        self.checks_run += 1
        node_ids = {n['id'] for n in nodes}

        for link in links:
            source = link.get('source')
            target = link.get('target')

            if source and source not in node_ids:
                self.warnings.append(
                    f"Dangling link source: {source} → {target} (source node not found)"
                )

            if target and target not in node_ids:
                self.warnings.append(
                    f"Dangling link target: {source} → {target} (target node not found)"
                )

        logger.info(f"  ✓ Checked link integrity")

    def _check_duplicates(self, nodes: List[Dict]) -> None:
        """Check for duplicate node IDs."""
        self.checks_run += 1
        seen_ids = defaultdict(int)

        for node in nodes:
            node_id = node.get('id')
            if node_id:
                seen_ids[node_id] += 1

        for node_id, count in seen_ids.items():
            if count > 1:
                self.warnings.append(f"Duplicate node ID: {node_id} appears {count} times")

        logger.info(f"  ✓ Checked for duplicates")
