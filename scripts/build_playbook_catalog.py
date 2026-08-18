#!/usr/bin/env python3
"""Build the searchable MkDocs catalog from canonical Playbooks packages."""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS_ROOT = REPOSITORY_ROOT / "Playbooks"
DOCS_ROOT = REPOSITORY_ROOT / "playbook-site" / "docs"
CATALOG_PATH = DOCS_ROOT / "data" / "playbooks.json"
GENERATED_PLAYBOOKS_ROOT = DOCS_ROOT / "playbooks"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FDE_PUBLICATION_PROCESS_URL = (
    "https://github.com/WebexCC-SA/FDE-Engagement/blob/main/"
    "Playbooks/publication-process.md"
)
FDE_PUBLICATION_PROCESS_LINK = re.compile(
    r"\(\.\./publication-process\.md(?P<fragment>#[^)]+)?\)"
)
FACET_NAMES = (
    "verticals",
    "channels",
    "features",
    "customer_journeys",
    "integrations",
)


def rewrite_repository_links(body: str) -> str:
    """Keep repository-level references valid after a README becomes index.md."""

    body = body.replace(
        "(../../Skills/",
        "(https://github.com/ciscoAISCG/webex-cx-ai/tree/main/Skills/",
    )
    return FDE_PUBLICATION_PROCESS_LINK.sub(
        lambda match: f"({FDE_PUBLICATION_PROCESS_URL}{match.group('fragment') or ''})",
        body,
    )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def date_string(value: Any, field: str) -> str:
    if isinstance(value, dt.datetime):
        raise ValueError(f"{field} must be a date without a time")
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError(f"{field} must use YYYY-MM-DD") from exc
    raise ValueError(f"{field} must use YYYY-MM-DD")


def string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"{field} must be an array of non-empty strings")
    return value


def validate_facets(
    playbook_id: str,
    classification: dict[str, Any],
    taxonomy_facets: dict[str, Any],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for facet in FACET_NAMES:
        values = string_list(
            classification.get(facet), f"{playbook_id}.classification.{facet}"
        )
        allowed = taxonomy_facets.get(facet)
        if not isinstance(allowed, list):
            raise ValueError(f"taxonomy facets.{facet} must be an array")
        unsupported = sorted(set(values) - set(allowed))
        if unsupported:
            raise ValueError(
                f"{playbook_id}.classification.{facet} has unsupported values: "
                + ", ".join(unsupported)
            )
        result[facet] = values

    for required in ("features", "customer_journeys"):
        if not result[required]:
            raise ValueError(
                f"{playbook_id}.classification.{required} needs at least one value"
            )
    return result


def copy_playbook_page(
    playbook_dir: Path, playbook_id: str, *, requires_rebinding: bool
) -> None:
    destination = GENERATED_PLAYBOOKS_ROOT / playbook_id
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(playbook_dir, destination)

    readme = destination / "README.md"
    if not readme.is_file():
        raise ValueError(f"{playbook_dir} is missing README.md")

    body = rewrite_repository_links(readme.read_text(encoding="utf-8"))
    package_url = (
        "https://github.com/WebexCC-SA/FDE-Playbook-Catalog/tree/main/"
        f"Playbooks/{playbook_id}"
    )
    notice = ""
    if requires_rebinding:
        notice = (
            "> **Catalog sample:** Imported from the public "
            "[`ciscoAISCG/webex-cx-ai` playbooks]"
            "(https://github.com/ciscoAISCG/webex-cx-ai/tree/main/Playbooks). "
            "Review and rebind tenant-specific references before use. "
            f"[View the canonical package files]({package_url}).\n\n"
        )
    (destination / "index.md").write_text(notice + body, encoding="utf-8")
    readme.unlink()


def build_catalog() -> dict[str, Any]:
    taxonomy = load_yaml(PLAYBOOKS_ROOT / "taxonomy.yaml")
    taxonomy_facets = taxonomy.get("facets")
    if not isinstance(taxonomy_facets, dict):
        raise ValueError("Playbooks/taxonomy.yaml is missing facets")

    records: list[dict[str, Any]] = []
    for playbook_dir in sorted(path for path in PLAYBOOKS_ROOT.iterdir() if path.is_dir()):
        manifest_path = playbook_dir / "manifest.yaml"
        readme_path = playbook_dir / "README.md"
        if not manifest_path.is_file() or not readme_path.is_file():
            continue

        manifest = load_yaml(manifest_path)
        playbook_id = manifest.get("id")
        if not isinstance(playbook_id, str) or not SLUG_PATTERN.fullmatch(playbook_id):
            raise ValueError(f"{manifest_path}: id must be a normalized slug")
        if playbook_id != playbook_dir.name:
            raise ValueError(f"{manifest_path}: id must match its directory name")

        title = manifest.get("title")
        summary = manifest.get("summary")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{manifest_path}: title must be a non-empty string")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(f"{manifest_path}: summary must be a non-empty string")

        classification = manifest.get("classification")
        if not isinstance(classification, dict):
            raise ValueError(f"{manifest_path}: classification must be a mapping")
        facets = validate_facets(playbook_id, classification, taxonomy_facets)

        complexity = manifest.get("complexity")
        allowed_complexity = taxonomy_facets.get("complexity", [])
        if complexity not in allowed_complexity:
            raise ValueError(
                f"{manifest_path}: complexity must be one of "
                + ", ".join(allowed_complexity)
            )

        security = manifest.get("security", {})
        requires_rebinding = not (
            isinstance(security, dict)
            and security.get("tenant_identifiers_removed") is True
        )
        copy_playbook_page(
            playbook_dir, playbook_id, requires_rebinding=requires_rebinding
        )
        records.append(
            {
                "id": playbook_id,
                "title": title.strip(),
                "summary": summary.strip(),
                "verticals": facets["verticals"],
                "channels": facets["channels"],
                "features": facets["features"],
                "customerJourneys": facets["customer_journeys"],
                "integrations": facets["integrations"],
                "complexity": complexity,
                "lastValidated": date_string(
                    manifest.get("last_validated"), f"{playbook_id}.last_validated"
                ),
                "keywords": string_list(
                    manifest.get("keywords"), f"{playbook_id}.keywords"
                ),
                "requiresRebinding": requires_rebinding,
                "url": f"playbooks/{playbook_id}/",
            }
        )

    catalog = {
        "schemaVersion": taxonomy.get("schema_version", 1),
        "facets": {
            name: taxonomy_facets.get(name, [])
            for name in (*FACET_NAMES, "complexity")
        },
        "playbooks": records,
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return catalog


if __name__ == "__main__":
    generated = build_catalog()
    print(f"Generated catalog with {len(generated['playbooks'])} playbook(s).")
