"""
Audit checklist for ETL pipeline - validates data quality before commit.
This prevents regressions and ensures all entities are properly handled.
"""

import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditChecklist:
    """Run comprehensive validation on transformed and filtered data."""

    def __init__(self, nodes_full: List[Dict], links_full: List[Dict],
                 nodes_filtered: List[Dict], links_filtered: List[Dict]):
        """Initialize with full and filtered graph data."""
        self.nodes_full = nodes_full
        self.links_full = links_full
        self.nodes_filtered = nodes_filtered
        self.links_filtered = links_filtered
        self.issues = []
        self.warnings = []

    def run_all_checks(self) -> Tuple[bool, List[str], List[str]]:
        """Run all audits. Returns (passed, issues, warnings)."""
        logger.info("\n" + "=" * 80)
        logger.info("RUNNING AUDIT CHECKLIST")
        logger.info("=" * 80)

        self._check_transformation_errors()
        self._check_data_loss_by_type()
        self._check_orphaned_nodes()
        self._check_id_format()
        self._check_filtering_statistics()
        self._check_reachability()

        passed = len(self.issues) == 0
        logger.info(f"\n{'✓ AUDIT PASSED' if passed else '✗ AUDIT FAILED'}")
        logger.info(f"Issues: {len(self.issues)}, Warnings: {len(self.warnings)}")

        return passed, self.issues, self.warnings

    def _check_transformation_errors(self):
        """Verify no nodes were lost due to transformation errors."""
        # Check for entities with empty labels (indicate failed transformation)
        empty_labels = [n for n in self.nodes_full if not n.get('label')]
        if empty_labels:
            self.warnings.append(
                f"Found {len(empty_labels)} nodes with empty labels (potential transformation errors)"
            )

    def _check_data_loss_by_type(self):
        """Compare data counts full → filtered by type."""
        type_counts_full = {}
        type_counts_filtered = {}

        for node in self.nodes_full:
            node_type = node.get('type', 'Unknown')
            type_counts_full[node_type] = type_counts_full.get(node_type, 0) + 1

        for node in self.nodes_filtered:
            node_type = node.get('type', 'Unknown')
            type_counts_filtered[node_type] = type_counts_filtered.get(node_type, 0) + 1

        logger.info("\nData Loss Analysis (full → filtered):")
        for node_type in sorted(type_counts_full.keys()):
            full_count = type_counts_full[node_type]
            filtered_count = type_counts_filtered.get(node_type, 0)
            loss_pct = ((full_count - filtered_count) / full_count * 100) if full_count > 0 else 0

            log_msg = f"  {node_type:20} {full_count:3} → {filtered_count:3} ({loss_pct:6.1f}% loss)"

            # Flag unexpected losses
            # Publications, Media, Projects should have 0% loss (now have implicit links)
            if node_type in ['Publication', 'Media', 'Project'] and loss_pct > 5:
                self.issues.append(
                    f"{node_type}: Lost {full_count - filtered_count} nodes ({loss_pct:.1f}%)"
                )
                logger.error(log_msg + " ← ISSUE")
            # Exhibitions/Locations can lose nodes if not connected to Jaime
            elif node_type in ['Exhibition', 'Location'] and loss_pct > 50:
                self.warnings.append(
                    f"{node_type}: High loss {loss_pct:.1f}% - verify if expected"
                )
                logger.warning(log_msg + " ← WARNING")
            else:
                logger.info(log_msg)

    def _check_orphaned_nodes(self):
        """Find nodes in filtered graph with no links."""
        node_ids = {n['id'] for n in self.nodes_filtered}
        linked_ids = set()

        for link in self.links_filtered:
            linked_ids.add(link['source'])
            linked_ids.add(link['target'])

        orphaned = node_ids - linked_ids
        if orphaned and orphaned != {'PER_0001'}:  # Jaime can be temporarily alone
            self.warnings.append(
                f"Found {len(orphaned)} orphaned nodes in filtered graph (no links)"
            )
            logger.warning(f"  Orphaned IDs: {sorted(orphaned)[:5]}...")

    def _check_id_format(self):
        """Detect non-standard ID formats."""
        valid_pattern_count = 0
        invalid_ids = []

        for node in self.nodes_full:
            node_id = node.get('id', '')
            # Valid format: TYPE_NNNN (e.g., PER_0001, EXP_0023)
            parts = node_id.split('_')
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 4:
                valid_pattern_count += 1
            else:
                if len(node_id) > 0:
                    invalid_ids.append(node_id)

        if invalid_ids:
            self.warnings.append(
                f"Found {len(invalid_ids)} non-standard IDs: {invalid_ids[:5]}"
            )
            logger.warning(f"  Non-standard IDs may cause validation issues")

    def _check_filtering_statistics(self):
        """Log filtering statistics."""
        total_loss_pct = (
            (len(self.nodes_full) - len(self.nodes_filtered)) /
            len(self.nodes_full) * 100
        ) if self.nodes_full else 0

        logger.info(f"\nFiltering Statistics:")
        logger.info(f"  Nodes: {len(self.nodes_full)} → {len(self.nodes_filtered)} ({total_loss_pct:.1f}% loss)")
        logger.info(f"  Links: {len(self.links_full)} → {len(self.links_filtered)}")

        # Warning if >40% of nodes lost (likely indicates filtering problem)
        if total_loss_pct > 40:
            self.warnings.append(
                f"High data loss in filtering: {total_loss_pct:.1f}% of nodes excluded"
            )

    def _check_reachability(self):
        """Verify PER_0001 (Jaime) is in filtered graph and has connections."""
        jaime_in_graph = any(n['id'] == 'PER_0001' for n in self.nodes_filtered)
        if not jaime_in_graph:
            self.issues.append("PER_0001 (Jaime) not found in filtered graph!")
            return

        # Count Jaime's connections
        jaime_links = [l for l in self.links_filtered
                      if l['source'] == 'PER_0001' or l['target'] == 'PER_0001']
        if not jaime_links:
            self.issues.append("PER_0001 (Jaime) has no connections in filtered graph!")

        logger.info(f"\nReachability Check:")
        logger.info(f"  PER_0001 in graph: {'✓' if jaime_in_graph else '✗'}")
        logger.info(f"  Direct connections: {len(jaime_links)}")
