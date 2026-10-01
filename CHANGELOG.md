# Changelog — Oregon Counties — Code, Ordinances, Policy and Land Use

Keep a Changelog format; ISO dates. Change types: Added, Source-Updated,
Superseded, Repealed, Removed, Verified, Fixed, Security.
Repo-curation dates only — official effective dates live in frontmatter.

## [Unreleased] — Yamhill and Curry recovered

### Source-Updated
- 2026-10-01 — Ten 404'd county sources (oregon-counties#85) triaged; relocated, removed, and
  could-not-determine, none withdrawn:
  - Wallowa 3 land-use/hazard-mitigation-plan volumes: the county's own comprehensive-plan-goals
    page still links the dead `vyhlif10466` CDN URLs for all three — not withdrawn, just stale
    on the county's own listing. Pointed at the current 2022-2027 edition of the same plan at
    the county's Natural Hazard Mitigation Plan page, but the old PDFs were never hashed or
    archived (no Wayback CDX captures), so byte-level identity with the new files cannot be
    shown — recorded as the current edition the county now publishes, not a confirmed move.
    The combined-plan entry's title/citation were corrected from an inferred "Volume I" to the
    county's own link text ("Wallowa County Multi-Jurisdictional Natural Hazard Mitigation Plan
    (2022-2027)"); it is one combined document, not a volume.
  - Klamath 1 (`2026-Classification-Tables---Non-Union`, found by a 2026-10-01 survey, not in
    the issue's original count of nine): DocumentCenter reassigned a new numeric id on
    re-upload. URL updated via the county's own Policies & Union Contracts listing, but its
    content also changed at the new id (not merely moved — out of scope for a 404 pass). The
    manifest's baseline sha256 is deliberately left at the OLD hash so drift detection reports
    it as changed and queues the re-ingest; re-ingesting the current table's text and updating
    the document's `source_url`/`source_sha256` is separate follow-up work.
  - Columbia 1: `columbia-orders-ordinances-2019-5-...` was a stale duplicate manifest entry
    for an ordinance already correctly tracked, with a working URL and a seeded baseline, under
    `columbia-orders-2019-5-...`. No document ever existed for the duplicate entry (sha256 was
    never seeded), so it is removed from the manifest (dedup, not a relocation) rather than
    "relocated" a second time; nothing in the corpus was deleted.
  - Multnomah 5 Pride Month proclamations (2020-2024): `multco.us`'s own `/file/.../download`
    link rotted for each (the Drupal file entity, not the catalogue record — the board-documents
    listing of record still names and dates every one). `multco.us`'s own news coverage of each
    links to a Granicus MetaViewer record of the same signed document, but
    `multnomah.granicus.com/robots.txt` serves a blanket `User-agent: * / Disallow: /`, and
    AGENTS.md's access exception (PLAN.md Phase 12) covers only ClaudeBot-specific directives on
    the text of county law — board proclamations aren't county law, and this isn't a
    ClaudeBot-specific directive. Recorded as could-not-determine rather than relocated; using
    the Granicus host needs an operator ruling first.
  - Wasco's 2 sources noted in the same survey are 403 (bot-blocked), not 404 — out of scope,
    tracked separately from this 404 pass.

### Notes
- 2026-10-01 — Re-measured #84: 29 ecode360.com sources are affected (clatsop 14, crook 15),
  not the 7 the issue title still says. Re-tested 2026-09-12, all 29 return a Cloudflare
  managed challenge (HTTP 403) to the honestly-identified fetcher, including the 22 that carry
  an August sha256 baseline — a baseline nobody can re-check is "could not check" wearing the
  clothes of "checked". Every ecode360 source in `_meta/sources/clatsop.yml` and `crook.yml`
  now carries a dated could-not-verify note; `crawl.decision` stays `proceed` (not
  `unavailable`, which is a group-wide stop that would also halt clatsop's 18 and crook's 3
  non-ecode360 sources this block does not touch — `src/ingest_counties.py`). No `sha256` was
  removed. This is a vendor (General Code) declining an honest crawler, never a county
  withdrawing anything it publishes, and never a 404. Verified Bots remains closed off
  permanently (home network, #116); General Code is not being contacted (considered, not
  chosen). Operator decision 2026-09-12 (route 3): ORS 192.311–192.478 records requests to
  Clatsop and Crook Counties, drafted for the operator to send (PR body).

### Fixed
- 2026-09-04 — `ingest_counties.py` re-ingesting an existing document dropped
  `relationships.references_external` back to `[]`, silently undoing
  `link_citations.py` work on every `--refetch` or re-run. The ingester now
  carries the existing document's `references_external` forward when the
  document already exists, and writes it back through `link_citations.rewrite`
  rather than through `write_document`'s YAML dump — the dump indents list
  items at the key's own indent, which `link_citations.py --check` does not
  recognise as current, so a re-ingest still failed the `generated` gate and a
  subsequent `link_citations.py` run duplicated the block instead of
  replacing it. A document whose existing frontmatter fails to parse is now
  re-ingested with an empty list (for `link_citations.py` to repopulate on its
  own next run) instead of counted as a failed source (#111).
- 2026-08-02 — `llms.txt` `## Contents` was still the template's empty stub — an
  advertised agent entry point serving an empty index (corpus-template#16).
  Filled with annotated entries for `counties/<slug>/`, the county registry,
  per-county source registries, the authority graph, and the mirrored ORS
  dispositions.

### Added
- **380 more scans recovered** (95% of 400 candidates): Yamhill 324, Curry 56. Corpus now
  **3,335 documents across 27 counties, 598 OCR-derived**, with 9,704 edges and 1,526
  documents citing state law.
- Yamhill 147 -> 497; its full 360-ordinance board record is now present rather than the 6%
  that happened to carry a text layer.
- Curry 2 -> 63; its entire county code, previously a complete blank.

### Notes
- Both families had been SKIPPED on the reasoning that publishing the readable minority would
  show an arbitrary, era-shaped slice of a countable set. That was correct when the choice
  was 6% or nothing; `ocr_recover.py` removed the trade-off, and the profiles now say so
  rather than carrying stale reasoning.
- 15 rejections (11 below the agreement bar, 4 under 100 words) and 6 fetch failures. Nothing
  was promoted that failed a gate.

## [Unreleased] — OCR recovery

### Added
- **188 image-only scans recovered into `## Full text`** under the two-engine rule, bringing
  the corpus to 2,929 documents (219 OCR-derived) across 27 counties and 8,658 edges.
- `src/ocr_recover.py` — ocrmypdf/tesseract plus PaddleOCR PP-OCRv6, run independently on the
  same scan. Gates: >=100 words, word agreement >=0.80, dictionary ratio >=0.80.
- `src/patterns.py` — draft-detection patterns shared by the discovery filter and the CI
  guardrail without either importing the other's dependencies.

### Notes
- Every OCR document carries an OCR-specific non-authoritative banner, `text_source: ocr`,
  both agreement rates and the dictionary ratio in `conversion_notes` ending `NOT
  human-verified`, and curator notes stating that agreement is evidence the words are on the
  page and **not** evidence they were read correctly.
- **Figure agreement is the weak point and is reported, never gated**: median 0.800 but
  16% of documents fall below 0.50. Dates, dollar amounts and ordinance numbers are the
  least trustworthy part of this text.
- 51 documents rejected (28 under 100 words, 23 below the agreement bar), 14 fetch failures,
  8 skipped. Nothing was promoted that failed a gate.

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
