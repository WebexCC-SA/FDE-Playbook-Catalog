from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from import_playbook import ImportFailure, import_playbook, load_changed_paths  # noqa: E402
from scg_taxonomy import ScgTaxonomyError  # noqa: E402


MANIFEST = """\
schema_version: 2
id: demo-playbook
title: Demo
summary: Safe demo package.
classification:
  features: [routing]
  customer_journeys: [routing-transfer]
complexity: beginner
last_validated: "2026-08-18"
ownership:
  owner: test-owner
  maintaining_team: fde-team
artifacts:
  flows:
    - flows/demo.json
security:
  customer_data_removed: true
  credentials_removed: true
  tenant_identifiers_removed: true
"""

SCG_TAXONOMY = {
    "schema_version": 2,
    "facets": {
        "verticals": ["retail"],
        "channels": ["voice"],
        "features": ["routing"],
        "customer_journeys": ["routing-transfer"],
        "integrations": ["rest-api"],
        "complexity": ["beginner"],
    },
    "display_labels": {
        "verticals": {"retail": "Retail"},
        "channels": {"voice": "Voice"},
        "features": {"routing": "Routing"},
        "customer_journeys": {"routing-transfer": "Routing and transfer"},
        "integrations": {"rest-api": "REST API"},
        "complexity": {"beginner": "Beginner"},
    },
}


class ImportPlaybookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.source = root / "source"
        self.catalog = root / "catalog"
        package = self.source / "Playbooks" / "demo-playbook"
        (package / "flows").mkdir(parents=True)
        (self.catalog / "Playbooks").mkdir(parents=True)
        (package / "manifest.yaml").write_text(MANIFEST, encoding="utf-8")
        (package / "README.md").write_text("# Demo\n", encoding="utf-8")
        (package / "flows" / "demo.json").write_text("{}\n", encoding="utf-8")
        self.taxonomy_loader = mock.patch(
            "import_playbook.load_scg_taxonomy", return_value=SCG_TAXONOMY
        )
        self.taxonomy_loader.start()

    def tearDown(self) -> None:
        self.taxonomy_loader.stop()
        self.temporary.cleanup()

    def test_imports_declared_package_without_local_taxonomy(self) -> None:
        playbook_id = import_playbook(
            self.source,
            self.catalog,
            ["Playbooks/demo-playbook/manifest.yaml"],
        )
        self.assertEqual(playbook_id, "demo-playbook")
        self.assertTrue(
            (self.catalog / "Playbooks" / "demo-playbook" / "flows" / "demo.json").is_file()
        )
        self.assertFalse((self.source / "Playbooks" / "taxonomy.yaml").exists())
        self.assertFalse((self.catalog / "Playbooks" / "taxonomy.yaml").exists())

    def test_rejects_a_local_taxonomy_change(self) -> None:
        (self.source / "Playbooks" / "taxonomy.yaml").write_text(
            "schema_version: 2\nfacets: {}\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ImportFailure, "outside one playbook package"):
            import_playbook(
                self.source,
                self.catalog,
                ["Playbooks/demo-playbook/manifest.yaml", "Playbooks/taxonomy.yaml"],
            )

    def test_stops_when_the_scg_taxonomy_cannot_be_loaded(self) -> None:
        with mock.patch(
            "import_playbook.load_scg_taxonomy",
            side_effect=ScgTaxonomyError("SCG taxonomy is unavailable"),
        ):
            with self.assertRaisesRegex(ImportFailure, "SCG taxonomy is unavailable"):
                import_playbook(
                    self.source,
                    self.catalog,
                    ["Playbooks/demo-playbook/manifest.yaml"],
                )

    def test_rejects_unlisted_file(self) -> None:
        (self.source / "Playbooks" / "demo-playbook" / "secret.txt").write_text(
            "do not publish", encoding="utf-8"
        )
        with self.assertRaisesRegex(ImportFailure, "unlisted files"):
            import_playbook(
                self.source,
                self.catalog,
                ["Playbooks/demo-playbook/manifest.yaml"],
            )

    def test_rejects_incomplete_security_attestation(self) -> None:
        manifest = self.source / "Playbooks" / "demo-playbook" / "manifest.yaml"
        manifest.write_text(
            MANIFEST.replace("tenant_identifiers_removed: true", "tenant_identifiers_removed: false"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ImportFailure, "security attestations"):
            import_playbook(
                self.source,
                self.catalog,
                ["Playbooks/demo-playbook/manifest.yaml"],
            )

    def test_rejects_more_than_one_playbook(self) -> None:
        with self.assertRaisesRegex(ImportFailure, "exactly one changed playbook"):
            import_playbook(
                self.source,
                self.catalog,
                [
                    "Playbooks/demo-playbook/manifest.yaml",
                    "Playbooks/another-playbook/manifest.yaml",
                ],
            )

    def test_loads_paginated_github_file_response(self) -> None:
        response = Path(self.temporary.name) / "files.json"
        response.write_text(
            json.dumps([[{"filename": "Playbooks/demo-playbook/README.md"}]]),
            encoding="utf-8",
        )
        self.assertEqual(
            load_changed_paths(response), ["Playbooks/demo-playbook/README.md"]
        )


if __name__ == "__main__":
    unittest.main()
