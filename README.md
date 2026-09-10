# FDE Playbook Catalog

Searchable catalog of Webex Contact Center playbooks.

Canonical packages live under `Playbooks/<playbook-id>/`. The catalog builder
reads each `manifest.yaml`, generates the search index, and copies its README
and supporting files into the MkDocs site. Only reviewed, customer-safe
playbooks should be added to the catalog.

## Local preview

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --requirement playbook-site/requirements.txt
python scripts/build_playbook_catalog.py
cd playbook-site
mkdocs serve
```

Open `http://127.0.0.1:8000/`.

## Taxonomy migrations

The catalog taxonomy must match the canonical
`WebexCC-SA/FDE-Engagement/Playbooks/taxonomy.yaml` contract. A normal
single-playbook import never replaces the catalog taxonomy implicitly.

When the canonical taxonomy changes:

1. Open a dedicated catalog pull request that updates
   `Playbooks/taxonomy.yaml` and migrates every existing manifest affected by
   removed or renamed values.
2. Run the importer tests, regenerate the catalog, and build MkDocs with
   strict validation.
3. Review and merge the taxonomy migration before retrying publication of a
   playbook that uses the new contract.

If the source and catalog taxonomies differ, the importer stops with a
`catalog taxonomy migration` error instead of mixing incompatible manifest
versions.
