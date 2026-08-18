# Catalog Publication Test

Verify the controlled cross-repository publication workflow without using customer data or production configuration.

## Summary

This synthetic playbook tests that a merged `FDE-Engagement` pull request with
the exact `publish:catalog` label creates a draft pull request in
`FDE-Playbook-Catalog`.

## Owner and maintenance

- Owner: `dbokatov`
- Maintaining team: `fde-team`
- Purpose: temporary workflow validation

Remove this package from `FDE-Engagement` through an unlabeled cleanup pull
request after the publication workflow has been verified.

## Applicability

Use this package only to test the playbook validation, GitHub App token,
cross-repository checkout, strict importer, generated catalog, and destination
pull-request creation.

Do not merge the generated catalog pull request because this is synthetic test
content.

## Prerequisites

- The source validation workflow is enabled on `FDE-Engagement`.
- The catalog importer and catalog validation workflow are present on catalog
  `main`.
- The publisher GitHub App is installed on both repositories.
- `PLAYBOOK_PUBLISHER_CLIENT_ID` and
  `PLAYBOOK_PUBLISHER_PRIVATE_KEY` are configured in the source repository.
- The exact `publish:catalog` label exists in the source repository.

## Implementation

1. Open a source pull request containing only this playbook directory.
2. Wait for **Validate playbooks / Validate playbook metadata and content** to
   pass.
3. Add the exact `publish:catalog` label.
4. Merge the source pull request.
5. Confirm **Publish playbook to catalog / Create catalog pull request** passes.
6. Locate the generated draft pull request in `FDE-Playbook-Catalog`.
7. Confirm **Validate Playbook Catalog / Test importer and build catalog**
   passes on that draft pull request.
8. Close the generated catalog pull request without merging it.
9. Remove this source package through a separate pull request without the
   publication label.

## Validation

Confirm all of the following:

- source validation succeeds;
- the publisher uses the merged source commit;
- one deterministic automation branch is created in the catalog;
- one draft catalog pull request is created;
- the source PR number and merged commit are included in the catalog PR body;
- the copied package contains only the README, manifest, and declared artifact;
- the catalog validation check succeeds.

The concise expected result is recorded in
[`validation/expected-result.txt`](validation/expected-result.txt).

## Security and privacy

This package contains no customer names, customer data, credentials, personal
data, tenant identifiers, executable exports, or proprietary configuration.
All content is synthetic.

The package must still receive normal human review. Boolean security
attestations do not independently detect sensitive content.

## Troubleshooting

- If source validation fails, inspect the manifest taxonomy values and required
  README sections.
- If token generation fails, verify the GitHub App installation and the exact
  repository variable and secret names.
- If the importer rejects the package, confirm that every file except
  `README.md` and `manifest.yaml` is declared under `artifacts`.
- If no draft catalog PR appears, inspect the source workflow and confirm that
  the source PR was merged with `publish:catalog` present.

## References

- [FDE playbook catalog publication process](../publication-process.md)
- [Catalog repository](https://github.com/WebexCC-SA/FDE-Playbook-Catalog)
