from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import URLError


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import scg_taxonomy  # noqa: E402


TAXONOMY_YAML = """\
schema_version: 2
facets:
  verticals: [retail]
  channels: [voice]
  features: [newly-added-feature]
  customer_journeys: [customer-service]
  integrations: [rest-api]
  complexity: [beginner]
display_labels:
  verticals: {retail: Retail}
  channels: {voice: Voice}
  features: {newly-added-feature: Newly added feature}
  customer_journeys: {customer-service: Customer service}
  integrations: {rest-api: REST API}
  complexity: {beginner: Beginner}
"""


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        return False

    def read(self, _amount: int) -> bytes:
        return TAXONOMY_YAML.encode("utf-8")


class ScgTaxonomyTests(unittest.TestCase):
    def test_fetches_and_parses_the_canonical_taxonomy(self) -> None:
        with mock.patch.object(
            scg_taxonomy, "urlopen", return_value=FakeResponse()
        ) as fetch:
            taxonomy = scg_taxonomy.load_scg_taxonomy()

        fetch.assert_called_once_with(scg_taxonomy.SCG_TAXONOMY_URL, timeout=15)
        self.assertEqual(taxonomy["facets"]["features"], ["newly-added-feature"])

    def test_stops_when_github_is_unavailable(self) -> None:
        with mock.patch.object(
            scg_taxonomy, "urlopen", side_effect=URLError("offline")
        ):
            with self.assertRaisesRegex(
                scg_taxonomy.ScgTaxonomyError, "do not use a local taxonomy copy"
            ):
                scg_taxonomy.load_scg_taxonomy()


if __name__ == "__main__":
    unittest.main()
