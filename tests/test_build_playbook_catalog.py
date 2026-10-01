from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import build_playbook_catalog as catalog_builder  # noqa: E402
from build_playbook_catalog import (  # noqa: E402
    FDE_PUBLICATION_PROCESS_URL,
    rewrite_repository_links,
)


SCG_TAXONOMY = {
    "schema_version": 2,
    "facets": {
        "verticals": ["retail"],
        "channels": ["voice"],
        "features": ["newly-added-feature"],
        "customer_journeys": ["customer-service"],
        "integrations": ["rest-api"],
        "complexity": ["beginner"],
    },
    "display_labels": {
        "verticals": {"retail": "Retail"},
        "channels": {"voice": "Voice"},
        "features": {"newly-added-feature": "Newly added feature"},
        "customer_journeys": {"customer-service": "Customer service"},
        "integrations": {"rest-api": "REST API"},
        "complexity": {"beginner": "Beginner"},
    },
}


MANIFEST = """\
schema_version: 2
id: dynamic-feature
title: Dynamic feature
summary: Validate a value supplied by the current SCG taxonomy.
classification:
  features: [newly-added-feature]
  customer_journeys: [customer-service]
complexity: beginner
last_validated: "2026-10-01"
security:
  customer_data_removed: true
  credentials_removed: true
  tenant_identifiers_removed: true
"""


class RepositoryLinkRewriteTests(unittest.TestCase):
    def test_rewrites_fde_publication_process_link(self) -> None:
        source = "[Publication process](../publication-process.md)"
        expected = f"[Publication process]({FDE_PUBLICATION_PROCESS_URL})"
        self.assertEqual(rewrite_repository_links(source), expected)

    def test_preserves_publication_process_fragment(self) -> None:
        source = "[Security](../publication-process.md#security-boundary)"
        expected = (
            f"[Security]({FDE_PUBLICATION_PROCESS_URL}#security-boundary)"
        )
        self.assertEqual(rewrite_repository_links(source), expected)

    def test_does_not_rewrite_other_parent_links(self) -> None:
        source = "[Another playbook](../another-playbook/)"
        self.assertEqual(rewrite_repository_links(source), source)

    def test_generated_page_uses_absolute_publication_process_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source" / "demo-playbook"
            generated = root / "generated"
            source.mkdir(parents=True)
            (source / "README.md").write_text(
                "[Publication process](../publication-process.md)\n",
                encoding="utf-8",
            )

            with mock.patch.object(
                catalog_builder, "GENERATED_PLAYBOOKS_ROOT", generated
            ):
                catalog_builder.copy_playbook_page(
                    source, "demo-playbook", requires_rebinding=False
                )

            result = (generated / "demo-playbook" / "index.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                result,
                f"[Publication process]({FDE_PUBLICATION_PROCESS_URL})\n",
            )


class ScgTaxonomyBuildTests(unittest.TestCase):
    def test_build_uses_a_fetched_taxonomy_without_a_local_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            playbooks = root / "Playbooks"
            package = playbooks / "dynamic-feature"
            package.mkdir(parents=True)
            (package / "manifest.yaml").write_text(MANIFEST, encoding="utf-8")
            (package / "README.md").write_text("# Dynamic feature\n", encoding="utf-8")
            docs = root / "docs"

            with (
                mock.patch.object(
                    catalog_builder, "PLAYBOOKS_ROOT", playbooks
                ),
                mock.patch.object(catalog_builder, "DOCS_ROOT", docs),
                mock.patch.object(
                    catalog_builder, "CATALOG_PATH", docs / "data" / "playbooks.json"
                ),
                mock.patch.object(
                    catalog_builder, "GENERATED_PLAYBOOKS_ROOT", docs / "playbooks"
                ),
                mock.patch.object(
                    catalog_builder, "load_scg_taxonomy", return_value=SCG_TAXONOMY
                ) as taxonomy_loader,
            ):
                result = catalog_builder.build_catalog()

            taxonomy_loader.assert_called_once_with()
            self.assertEqual(result["facets"]["features"], ["newly-added-feature"])
            self.assertEqual(result["playbooks"][0]["id"], "dynamic-feature")


if __name__ == "__main__":
    unittest.main()
