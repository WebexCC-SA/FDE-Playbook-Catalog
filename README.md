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

## Taxonomy

The canonical schema-v2 taxonomy is fetched from
[`ciscoAISCG/webex-cx-ai`](https://raw.githubusercontent.com/ciscoAISCG/webex-cx-ai/main/Playbooks/taxonomy.yaml)
for every import and catalog build. The repository intentionally contains no
taxonomy copy.

If the taxonomy cannot be retrieved or parsed, the importer and catalog build
stop safely. Restore GitHub/network access and retry; do not add a local
taxonomy fallback.
