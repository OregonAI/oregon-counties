# Changelog — Oregon Counties — Code, Ordinances, Policy and Land Use

Keep a Changelog format; ISO dates. Change types: Added, Source-Updated,
Superseded, Repealed, Removed, Verified, Fixed, Security.
Repo-curation dates only — official effective dates live in frontmatter.

## [Unreleased] — tranche 2

### Added
- Six more counties by population: Yamhill 147, Polk 104, Benton 52, Umatilla 37, Coos 30,
  Klamath 22. Corpus now holds **1,621 documents across 12 counties**.
- 4,882 `references_external` edges into `executive-regulatory-frameworks`; 683 documents
  (42%) cite ORS or OAR.
- `index_url` + `index_re` discovery, for counties whose code page lists Title PAGES rather
  than documents (Polk). Without it Polk's code discovers one document and reports success.
- `explicit` families, for a family of one or two known documents where discovery would
  produce worse metadata than declaring it.
- `dedupe: name-highest-id`, for CivicPlus re-uploads that leave the same instrument linked
  twice under different DocumentCenter ids.
- HTTP 429 backoff honouring `Retry-After`. 429 means "slow down", not "refused", and
  treating it as a refusal both lost documents and misstated the host's position.

### Notes
- Marion, Linn, Douglas and Josephine moved to the END of the build order, recorded in
  `_meta/counties.yml` under `deferred:`. Each returns HTTP 403 (Cloudflare managed
  challenge) to an honestly-identified agent. ~588,000 people, 14% of Oregon.
- Yamhill's 360 adopted ordinances are **94% scanned images** (338 of 360 extract to zero
  characters). The family is skipped rather than partially ingested — publishing the 6% that
  carry text would show an arbitrary slice under a healthy-looking count. Needs OCR; not an
  absence at Yamhill.
- Umatilla's comprehensive plan URL, recorded live by the survey on 2026-07-31, now 404s —
  the migration hazard that county's profile warns about, arriving within a day.

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
