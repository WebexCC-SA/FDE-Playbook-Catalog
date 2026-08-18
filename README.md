# FDE Playbook Catalog

Searchable catalog of validated Webex Contact Center playbooks.

This repository currently contains synthetic demonstration content used to
validate the catalog experience. It must not contain customer names, tenant
identifiers, credentials, internal Jira references, or production
configuration.

## Local preview

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --requirement playbook-site/requirements.txt
cd playbook-site
mkdocs serve
```

Open `http://127.0.0.1:8000/`.
