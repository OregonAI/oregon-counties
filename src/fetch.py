"""This corpus's fetch adapter over the toolkit's fetcher (corpus-toolkit ADR-0016).

The fetcher that used to live here -- honest agent, HTTP/2, per-host interval, 429 backoff
honouring Retry-After, `Refused`/`Challenge` kept distinct from a 404, TLS-chain failures
named for what they are -- is now `corpus_toolkit.sources.fetch`, war stories included; it
was lifted from this file because it was the one fetcher on the platform that had met
hostile hosts. What remains here is what is THIS corpus's:

  - `source_dates`: `as_of` tracks `retrieved`. Unlike eCFR, no county pins a date in its
    URL -- the file at that address is whatever is there today, so the date we pulled it is
    the best available statement of what the text is as of. Inventing more precision would
    be a fabricated effective date on a legal instrument.
  - `looks_like_draft`: the draft-filename patterns, from `src/patterns.py` (which imports
    nothing, so `check_guardrails.py` can share them without the HTTP stack).
  - The crawl DECISION is recorded per source in `_meta/sources/<county>.yml` under
    `crawl:`, reviewable in a PR. robots.txt is reported by the toolkit, not enforced; the
    operator's decision (PLAN.md Phase 12) stands as recorded there.

The module keeps its old call shape (`get(url) -> (body, content_type)`, `snapshot`, `sniff`,
`UNSUPPORTED`, `Refused`, `Challenge`, `USER_AGENT`) so the callers did not change.
"""
from __future__ import annotations

import pathlib
import re

from corpus_toolkit import config as config_mod
from corpus_toolkit.sources.fetch import (  # noqa: F401  (re-exported for callers)
    UNSUPPORTED, Challenge, FetchError, Fetcher, Refused, sniff,
)
from corpus_toolkit.sources.snapshots import recorded_retrieved, retrieved_date
from src.patterns import DRAFT_PATTERNS

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = config_mod.load(ROOT / "_meta" / "corpus.yml")

FETCHER = Fetcher(CONFIG)
USER_AGENT = FETCHER.user_agent


def get(url: str) -> tuple[bytes, str]:
    """Fetch once, honestly, over HTTP/2. Returns (body, content_type). Raises
    `Refused`/`Challenge` -- see corpus_toolkit.sources.fetch for why those are kept
    distinct from a 404, and from each other."""
    got = FETCHER.get(url)
    return got.body, got.content_type


def snapshot(url: str, dest: pathlib.Path, refetch: bool = False) -> tuple[bytes, bool]:
    """Fetch to `dest` unless it already exists. Returns (bytes, fresh)."""
    return FETCHER.snapshot(url, dest, refetch)


def source_dates(snap: pathlib.Path, fresh: bool, doc_path: pathlib.Path) -> tuple[str, str]:
    """(as_of, retrieved) -- from the SOURCE, never from the wall clock. `retrieved`
    advances only when bytes were actually fetched; `as_of` tracks it (see module doc)."""
    retrieved = retrieved_date(fresh, doc_path, snap)
    return retrieved, retrieved


def looks_like_draft(name: str) -> bool:
    return any(re.search(p, name, re.I) for p in DRAFT_PATTERNS)
