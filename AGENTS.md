# AGENTS.md — Oregon Counties — Code, Ordinances, Policy and Land Use

Corpus of the OregonAI civic corpus platform. Archetype: document.
Read `_meta/corpus.yml` for configuration; the platform rules live in
OregonAI/corpus-toolkit `docs/`.

## Purpose
Non-authoritative, AI-friendly mirror of policy instruments of Oregon's 36 counties — codified county code and ordinances, board and county-court orders, administrative policy (HR, purchasing, public records, IT), and land use (comprehensive plans, zoning, development codes).
Never a source of truth — every answer must cite and link the
authoritative source.

## Hard rules (anti-fabrication)
1. Never write content that does not exist in the pinned source. Source
   unreachable or unparseable → insert
   `<!-- TODO: human verification required -->` and stop. Never
   reconstruct from model knowledge.
2. `## Full text` sections are verbatim only. Curator content is confined
   to `## At a glance`, `## Curator notes`, `## Cross-references`.
3. Third-party copyrighted material: summary + official link only.
4. Never invent or infer a citation. Unresolvable → say so.
5. Live-data answers (api/hybrid) must carry the executed query and
   timestamp.
6. All changes via PR. Do not set `last_verified`/`verified_by` to a real
   value — the human reviewer does that at approval. The schema REQUIRES both
   keys, so ingestion writes them as empty strings: schema-valid, and read
   downstream as "never verified", which is exactly true. Never write a date or
   a handle you did not earn; a fabricated verification stamp is worse than an
   obviously-empty one.
7. Update this knowledge body's CHANGELOG.md in the same PR as content
   changes.

## Found a bug you are not fixing right now? Open an issue. Period.

This is not optional and has no size threshold.

If you discover a defect and do not fix it in the change you are working on, **open a
GitHub issue before you finish the task**. Not a note in the commit message, not a
paragraph in the PR body, not a line in your summary to the user. Those are not a work
queue — nobody greps closed PRs six months later, and the next agent rediscovers the same
bug from scratch, usually the expensive way.

This applies to every one of these, not just crashes:

- a check that passes without checking anything
- a documented command, flag, or path that does not exist or does not work
- a claim in a README, docstring, or catalog note that is no longer true
- data known to be wrong, stale, or incomplete
- a guard that cannot fire, or fires on the wrong condition
- something you worked around instead of fixing

**File it in the repo that owns the fix, which may not be the repo you are in.** A parser
defect here, a registry gap in a sibling corpus, and a validator gap in `corpus-toolkit`
are three different issues in three different repos. Say plainly in each which repo the
work belongs to.

An issue must answer four things, because an issue that only says "X is broken" costs the
next person the whole investigation again:

1. **What is wrong** — the specific behaviour, not a category
2. **How it was found** — the command, the data, the failing case
3. **What it breaks** — who or what gets a wrong answer, and how silently
4. **What would fix it**, or what still needs measuring before anyone can know

Prefer counts and reproductions over adjectives. "126 appropriations unjoined, of which 59
are an extraction gap and 41 are correct" is actionable; "agency matching needs work" is
not, and will be re-derived by someone else.

If you genuinely cannot open one — no network, no permission — say so explicitly in your
final message to the user and hand them the text to file. Silently dropping it is the one
outcome that is never acceptable.

## Workflow
Discovery → human-approved source manifest → ingestion → human-reviewed
PR. See toolkit `docs/replication-guide.md`.


## County rules — enforced, not honour-system

`src/check_guardrails.py` runs on every PR. Five rules, each about MEANING rather than
schema, which is why the toolkit's validators cannot see them:

| rule | fails the build when |
|---|---|
| governing body | a document in one of the 6 County Court counties names a Board of Commissioners, or the reverse |
| authority basis | a general-law county claims `authority_level: county_charter` (8 of 36 are charter; 28 are not) |
| absence is measured | `## At a glance` asserts a county publishes none of something without a matching `none-found` in the survey |
| no silent truncation | a line starts `## ` at column zero after `## Full text` — everything past the first is invisible to provenance, search and extract_fulltext |
| no drafts as law | a filename or source_url matches a redline/proposed pattern while `status: current` |

**Absence is the rule that matters most.** A county with no document here may publish none,
may not publish it online, or may sit behind a wall we could not pass. This corpus is least
entitled to infer the first from an empty directory. The claim must rest on
`corpus-seeds/oregon-counties.survey.yml`, which measured it.

## Access, and the line this corpus holds

Five source hosts serve `User-agent: ClaudeBot` / `Disallow: /`. The operator's decision
(PLAN.md Phase 12) is that such a directive is not binding for the TEXT OF COUNTY LAW, since
the county authors its law and the vendor hosts it.

That is not a licence to get in by any means. **Declining to honour a stated preference is
not the same act as disguising identity to defeat a technical access control.** `src/fetch.py`
sends an honest, self-identifying User-Agent and never a browser string. A host that refuses
it makes that source `unavailable` — recorded as a fact about our access, never as an absence
at the county. See `src/profiles/marion.py` for the case where that cost us a whole county,
and `src/profiles/washington.py` for the case where it cost nothing.

Every determination is recorded per host in `_meta/sources/<county>.yml` under `crawl:`, so
it is reviewable in a PR rather than buried in a fetcher.

## Generated files — never hand-edit

| file | generated by | gate |
|---|---|---|
| `_meta/graph.json` | `src/build_graph.py` | `generated` job, every PR |
| `relationships.references_external` | `src/link_citations.py` | `generated` job, every PR |
| `STATUS.md` | `corpus-generate-status` | `generated` job, every PR (plus a weekly repair in the `drift` job) |

Regenerate at the source and commit the result.

`_meta/corpus-index.json` is generated too but is **not committed**: `publish-index.yml`
builds it at deploy time. A committed copy can silently fall behind its own corpus, and
the damage lands in a SIBLING repo whose citation resolution reads it. Publish it; do
not commit it.

**Every generated file you commit needs a step in the `generated` job.** One without a
step is exactly the failure that job exists to prevent, and it is silent by construction
— the toolkit only READS these artifacts, so nothing anywhere notices when one goes
stale. A corpus that ships `joins:` owes itself the same treatment: the toolkit resolves
each `joins[].document_id`, but only this corpus can check that a `{dataset, key}` pair
selects any rows at all.

## OCR — the default stack is tesseract + PaddleOCR

When a source PDF has no text layer (`0 chars extracted`), this is the stack. Do not
hand-roll a renderer, and do not substitute a hosted or generative model.

**Primary: `ocrmypdf` (tesseract).** Writes a text layer into a COPY beside the
original — never over it, so `source_sha256` keeps hashing the bytes upstream served.

```
ocrmypdf -l eng --optimize 0 --output-type pdf --rotate-pages --deskew in.pdf out.pdf
```

**Cross-check: PaddleOCR (PP-OCRv6).** Reads the ORIGINAL scan, so the two engines
share nothing but the pixels — corroborating against the other engine's output is an
echo, not evidence. Measured word-sequence agreement across the six oregon-kpm scans:
**0.82–0.93**, every one clearing the 0.80 bar.

**Tiebreaker: docTR (DBNet + CRNN).** Not the default — it agrees with tesseract less
than Paddle does on every document (0.75–0.86), so it would lower every score. Reach
for it when the primary pair disagrees, and when orientation is in doubt: it straightens
pages itself and was the only engine that read a 180°-rotated scan correctly with no
document-specific retry.

**Every engine needs its orientation handling verified separately**, or the
corroboration check quietly becomes an orientation check. Measured: with Paddle's
`use_doc_orientation_classify=False`, a rotated scan scored **0.050** against tesseract;
with it on, **0.929**. Same page, same engines. Tesseract needs
`--rotate-pages-threshold 0` on that document — at default OSD confidence it leaves page
1 upside down and emits `:Peusiiqnd` for `Published:`, thousands of characters of
confident garbage that passes every length check.

**`pdftotext -layout` (poppler) is for a different fault** — a text layer that extracts
letter-spaced (`A c t u a l 9 3 %`) or in column rather than reading order. That is not
a scan; OCR is the wrong tool, and re-extracting with another engine recovers the real
spacing instead of guessing it back.

### Promotion into `## Full text`

Governed by the **two-engine rule** in `oregon-policy-repo/AGENTS.md`. A single
engine's output is never promotable. Reference implementations:
`oregon-policy-repo/src/ocr_fallback_eo.py` and `oregon-kpm/src/ocr_corroborate.py`.

Two traps worth inheriting, both found by measurement:

* **Never build the dictionary from a corpus that already contains OCR output.** The
  errors enter the vocabulary that judges them — `pernitted` becomes a recognised word —
  and every OCR'd document scores 100% dictionary-recognizable however badly it was
  read. A gate that cannot fail is worse than no gate, because it looks like evidence.
  Exclude `text_source: ocr` documents when building the vocabulary.
* **Score the figures separately from the words.** The reference metric counts
  `[a-z]{2,}` and so excludes every digit. On the oregon-kpm scans, word agreement ran
  88–98% while agreement on the FIGURES ran **69–85%** — digits are exactly where two
  engines diverge, and the headline number hides it. In any corpus whose payload is
  numbers, report both; a low figure score means human review, not rejection.

**OCR text is a machine reading of an image, not the source's own text.** Agreement is
evidence the words are on the page. It is NOT evidence they were read correctly, and two
engines can misread the same smudged digit identically. Record the engines, both
agreement rates and the dictionary ratio in `conversion_notes`, end with
`NOT human-verified`, and warn the reader in the document body.
