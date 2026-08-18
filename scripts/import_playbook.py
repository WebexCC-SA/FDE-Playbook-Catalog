#!/usr/bin/env python3
"""Import one approved FDE playbook package into the public catalog.

The script is intentionally strict: a publication may change exactly one
``Playbooks/<id>/`` package, plus the central taxonomy. Only README.md,
manifest.yaml, and files explicitly declared under ``artifacts`` are copied.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

import yaml


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECURITY_ATTESTATIONS = (
    "customer_data_removed",
    "credentials_removed",
    "tenant_identifiers_removed",
)
ALLOWED_SHARED_PATHS = {"Playbooks/taxonomy.yaml"}


class ImportFailure(RuntimeError):
    """Raised when a source package is unsafe or outside the copy contract."""


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise ImportFailure(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ImportFailure(f"{path} must contain a YAML mapping")
    return value


def load_changed_paths(path: Path) -> list[str]:
    """Read a GitHub API JSON response (including --paginate --slurp output)."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportFailure(f"cannot read changed-files JSON {path}: {exc}") from exc

    pages: Iterable[Any]
    if isinstance(value, list) and value and all(isinstance(item, list) for item in value):
        pages = (entry for page in value for entry in page)
    elif isinstance(value, list):
        pages = value
    else:
        raise ImportFailure("changed-files JSON must contain an array")

    filenames: list[str] = []
    for entry in pages:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str):
            raise ImportFailure("each changed-file entry must contain a filename")
        filenames.append(entry["filename"])
    if not filenames:
        raise ImportFailure("the source PR contains no changed files")
    return filenames


def changed_playbook_id(changed_paths: Sequence[str]) -> str:
    playbook_ids: set[str] = set()
    unexpected: list[str] = []

    for raw_path in changed_paths:
        posix_path = PurePosixPath(raw_path)
        if posix_path.is_absolute() or ".." in posix_path.parts:
            unexpected.append(raw_path)
            continue
        normalized = posix_path.as_posix()
        if normalized in ALLOWED_SHARED_PATHS:
            continue
        if len(posix_path.parts) >= 3 and posix_path.parts[0] == "Playbooks":
            playbook_id = posix_path.parts[1]
            if SLUG_PATTERN.fullmatch(playbook_id):
                playbook_ids.add(playbook_id)
                continue
        unexpected.append(raw_path)

    if unexpected:
        raise ImportFailure(
            "the publication PR changes files outside one playbook package: "
            + ", ".join(sorted(unexpected))
        )
    if len(playbook_ids) != 1:
        found = ", ".join(sorted(playbook_ids)) or "none"
        raise ImportFailure(
            f"publication requires exactly one changed playbook; found: {found}"
        )
    return next(iter(playbook_ids))


def artifact_paths(manifest: dict[str, Any]) -> list[PurePosixPath]:
    raw_artifacts = manifest.get("artifacts")
    if raw_artifacts is None:
        return []
    if not isinstance(raw_artifacts, dict):
        raise ImportFailure("manifest artifacts must be a mapping of path arrays")

    result: list[PurePosixPath] = []
    for group, values in raw_artifacts.items():
        if not isinstance(group, str) or not isinstance(values, list):
            raise ImportFailure("every artifact group must be a named path array")
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ImportFailure(f"artifacts.{group} contains an invalid path")
            artifact = PurePosixPath(value)
            if artifact.is_absolute() or ".." in artifact.parts:
                raise ImportFailure(f"artifact path escapes the package: {value}")
            if artifact.as_posix() in {"README.md", "manifest.yaml"}:
                raise ImportFailure(f"artifact path is reserved: {value}")
            result.append(artifact)

    if len(result) != len(set(result)):
        raise ImportFailure("manifest contains duplicate artifact paths")
    return result


def validate_source_package(source_root: Path, playbook_id: str) -> tuple[Path, list[PurePosixPath]]:
    package = source_root / "Playbooks" / playbook_id
    manifest_path = package / "manifest.yaml"
    readme_path = package / "README.md"
    if package.is_symlink() or not package.is_dir():
        raise ImportFailure(f"source package is missing or is a symlink: {package}")
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ImportFailure(f"source package needs a regular manifest.yaml: {package}")
    if not readme_path.is_file() or readme_path.is_symlink():
        raise ImportFailure(f"source package needs a regular README.md: {package}")

    manifest = load_yaml(manifest_path)
    if manifest.get("id") != playbook_id:
        raise ImportFailure("manifest id must match the source package directory")

    security = manifest.get("security")
    if not isinstance(security, dict):
        raise ImportFailure("manifest security must be a mapping")
    missing_attestations = [
        name for name in SECURITY_ATTESTATIONS if security.get(name) is not True
    ]
    if missing_attestations:
        raise ImportFailure(
            "publication requires true security attestations: "
            + ", ".join(missing_attestations)
        )

    artifacts = artifact_paths(manifest)
    expected_files = {PurePosixPath("README.md"), PurePosixPath("manifest.yaml"), *artifacts}
    actual_files: set[PurePosixPath] = set()
    for candidate in package.rglob("*"):
        if candidate.is_symlink():
            raise ImportFailure(f"symbolic links are not publishable: {candidate}")
        if candidate.is_file():
            actual_files.add(PurePosixPath(candidate.relative_to(package).as_posix()))

    missing = sorted(str(path) for path in expected_files - actual_files)
    unlisted = sorted(str(path) for path in actual_files - expected_files)
    if missing:
        raise ImportFailure("manifest references missing files: " + ", ".join(missing))
    if unlisted:
        raise ImportFailure("package contains unlisted files: " + ", ".join(unlisted))
    return package, artifacts


def regular_taxonomy(source_root: Path) -> Path:
    taxonomy = source_root / "Playbooks" / "taxonomy.yaml"
    if not taxonomy.is_file() or taxonomy.is_symlink():
        raise ImportFailure("source Playbooks/taxonomy.yaml must be a regular file")
    load_yaml(taxonomy)
    return taxonomy


def import_playbook(
    source_root: Path,
    catalog_root: Path,
    changed_paths: Sequence[str],
) -> str:
    source_root = source_root.resolve()
    catalog_root = catalog_root.resolve()
    playbook_id = changed_playbook_id(changed_paths)
    package, artifacts = validate_source_package(source_root, playbook_id)
    taxonomy = regular_taxonomy(source_root)

    catalog_playbooks = catalog_root / "Playbooks"
    if not catalog_playbooks.is_dir():
        raise ImportFailure(f"catalog Playbooks directory is missing: {catalog_playbooks}")
    target = catalog_playbooks / playbook_id

    with tempfile.TemporaryDirectory(prefix=".playbook-import-", dir=catalog_playbooks) as temp:
        staged = Path(temp) / playbook_id
        staged.mkdir()
        for relative in (PurePosixPath("README.md"), PurePosixPath("manifest.yaml"), *artifacts):
            source = package.joinpath(*relative.parts)
            destination = staged.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        if target.exists():
            if target.is_symlink() or not target.is_dir():
                raise ImportFailure(f"catalog target is not a regular directory: {target}")
            shutil.rmtree(target)
        shutil.move(str(staged), target)

    shutil.copy2(taxonomy, catalog_playbooks / "taxonomy.yaml")
    return playbook_id


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--catalog-root", type=Path, required=True)
    parser.add_argument("--changed-files-json", type=Path, required=True)
    parser.add_argument("--result-json", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        changed_paths = load_changed_paths(args.changed_files_json)
        playbook_id = import_playbook(
            args.source_root, args.catalog_root, changed_paths
        )
    except ImportFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = {"playbook_id": playbook_id}
    if args.result_json:
        args.result_json.write_text(json.dumps(result) + "\n", encoding="utf-8")
    print(f"Imported Playbooks/{playbook_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
