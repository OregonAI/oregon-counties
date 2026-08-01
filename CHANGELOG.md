# Changelog — Oregon Counties — Code, Ordinances, Policy and Land Use

Keep a Changelog format; ISO dates. Change types: Added, Source-Updated,
Superseded, Repealed, Removed, Verified, Fixed, Security.
Repo-curation dates only — official effective dates live in frontmatter.

## [Unreleased]

### Added
- Phase 12 first build: 1,229 documents across the 6 largest Oregon counties by population
  (Deschutes 784, Jackson 151, Clackamas 102, Multnomah 93, Lane 70, Washington 29).
- 3,131 `references_external` edges into `executive-regulatory-frameworks`; 469 documents
  (38%) cite ORS or OAR. Densest citations are the land-use regime — ORS 215.203, 197.732,
  OAR 660-012-0060 — confirming the seed's prediction rather than asserting it.
- Per-county profile modules (`src/profiles/<county>.py`), auto-discovered, one per county.
- `src/check_guardrails.py`: five CI-enforced rules, each negative-tested by deliberately
  breaking it.

### Notes
- Marion County is recorded `unavailable`: codepublishing.com returns HTTP 403 (Cloudflare
  managed challenge) to an honestly-identified agent. A fact about our access, not an
  absence at Marion County.
- Skipped families each carry their reason in `_meta/sources/<county>.yml`. Nothing is
  omitted silently.

## [Unreleased]
