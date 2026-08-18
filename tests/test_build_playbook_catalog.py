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


if __name__ == "__main__":
    unittest.main()
