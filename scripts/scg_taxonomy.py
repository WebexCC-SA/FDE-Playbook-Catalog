"""Load the canonical schema-v2 SCG taxonomy for catalog operations."""

from __future__ import annotations

from typing import Any
from urllib.request import urlopen

import yaml


SCG_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/ciscoAISCG/webex-cx-ai/main/"
    "Playbooks/taxonomy.yaml"
)
MAX_TAXONOMY_BYTES = 1_000_000
SCHEMA_VERSION = 2
REQUIRED_FACETS = (
    "verticals",
    "channels",
    "features",
    "customer_journeys",
    "integrations",
    "complexity",
)


class ScgTaxonomyError(RuntimeError):
    """Raised when the canonical taxonomy cannot be retrieved or validated."""


def load_scg_taxonomy() -> dict[str, Any]:
    """Fetch and parse the canonical taxonomy without a repository fallback."""
    try:
        with urlopen(  # noqa: S310 - fixed canonical URL
            SCG_TAXONOMY_URL, timeout=15
        ) as response:
            payload = response.read(MAX_TAXONOMY_BYTES + 1)
    except OSError as exc:
        raise ScgTaxonomyError(
            "could not fetch the SCG taxonomy from "
            f"{SCG_TAXONOMY_URL}: {exc}. Retry when GitHub/network access is "
            "available; do not use a local taxonomy copy."
        ) from exc

    if len(payload) > MAX_TAXONOMY_BYTES:
        raise ScgTaxonomyError(
            "SCG taxonomy exceeds "
            f"{MAX_TAXONOMY_BYTES} bytes: {SCG_TAXONOMY_URL}"
        )
    try:
        value = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ScgTaxonomyError(
            f"could not parse the SCG taxonomy from {SCG_TAXONOMY_URL}: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise ScgTaxonomyError("SCG taxonomy must contain a YAML mapping")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ScgTaxonomyError(
            f"SCG taxonomy schema_version must be {SCHEMA_VERSION}"
        )

    facets = value.get("facets")
    labels = value.get("display_labels")
    if not isinstance(facets, dict) or not isinstance(labels, dict):
        raise ScgTaxonomyError(
            "SCG taxonomy must contain facets and display_labels mappings"
        )
    for name in REQUIRED_FACETS:
        values = facets.get(name)
        facet_labels = labels.get(name)
        if not isinstance(values, list) or not all(
            isinstance(item, str) and item for item in values
        ):
            raise ScgTaxonomyError(
                f"SCG taxonomy facets.{name} must be an array of non-empty strings"
            )
        if not isinstance(facet_labels, dict) or set(values) != set(facet_labels):
            raise ScgTaxonomyError(
                f"SCG taxonomy display_labels.{name} must match facets.{name}"
            )
        if not all(
            isinstance(label, str) and label.strip()
            for label in facet_labels.values()
        ):
            raise ScgTaxonomyError(
                f"SCG taxonomy display_labels.{name} must use non-empty labels"
            )
    return value
