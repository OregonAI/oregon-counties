"""Fetching, for 36 counties on a dozen unrelated platforms.

THE IDENTITY THIS SENDS IS A DECISION, NOT A DEFAULT. Five of the source hosts this corpus
reaches serve `User-agent: ClaudeBot / Disallow: /`, several with
`Content-Signal: ai-train=no`. The operator's decision (PLAN.md Phase 12) is to ingest the
text of county law anyway, on the basis that the county authors its law and the vendor hosts
it. That decision is recorded per source in `_meta/sources/<county>.yml` under `crawl:`, so
it is reviewable in a PR rather than buried here.

The line this module holds inside that decision: **declining to honour a robots directive is
not the same as evading a technical access control.** So:

  - USER_AGENT identifies the project truthfully and links to it. It is not a browser
    string. Verified 2026-07-31 that library.municode.com and api.municode.com both return
    HTTP 200 to exactly this agent, so no spoofing is needed for the one host that prompted
    the decision.
  - A host that answers 401/403/429 to an honest agent has refused us at the HTTP layer.
    That source is UNAVAILABLE and is recorded as such. We do not then retry wearing a
    Chrome fingerprint. `Refused` is raised so the caller cannot mistake it for a 404.
  - One request per source, cached on disk forever after. Re-fetching is opt-in
    (`--refetch`), never a side effect of running the ingester again.
  - MIN_INTERVAL between requests to the same host, always.
"""
from __future__ import annotations

import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = ("OregonAI-CivicCorpus/1.0 "
              "(+https://github.com/OregonAI/oregon-counties; public-records archival)")

HEADERS = {"User-Agent": USER_AGENT,
           "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9",
           "Connection": "close"}

TIMEOUT = 120
MIN_INTERVAL = 2.0          # seconds between requests to the SAME host
_last: dict[str, float] = {}


class Refused(Exception):
    """The host refused an honestly-identified request (401/403/429, or a JS challenge).

    Distinct from a 404 on purpose. A missing document is a fact about the county; a refusal
    is a fact about our access, and the survey keeps `none-found` and `could-not-verify`
    apart for exactly this reason. Collapsing them is how a coverage number becomes a false
    claim about Oregon.
    """


class Challenge(Refused):
    """A bot-challenge interstitial, which does not look like a refusal by status code.

    Sucuri CloudProxy answers HTTP 307 with NO Location header and a ~1.3 KB JavaScript
    cookie page — Harney County's entire site is behind one. Cloudflare managed challenges
    answer 403 with `cf-mitigated: challenge`. Both are indistinguishable from a dead link
    unless you look, and both mean the opposite of one.
    """


def _throttle(url: str) -> None:
    host = urllib.parse.urlsplit(url).netloc
    wait = MIN_INTERVAL - (time.monotonic() - _last.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()


def get(url: str) -> tuple[bytes, str]:
    """Fetch once, honestly. Returns (body, content_type). Raises Refused/Challenge."""
    _throttle(url)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
            if resp.status == 307 and not resp.headers.get("Location"):
                raise Challenge(f"{url}: 307 with no Location — bot challenge")
            return body, ctype
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            mitigated = (e.headers or {}).get("cf-mitigated", "")
            raise (Challenge if mitigated == "challenge" else Refused)(
                f"{url}: HTTP {e.code}"
                f"{' (Cloudflare managed challenge)' if mitigated else ''}") from e
        if e.code == 307:
            raise Challenge(f"{url}: 307 challenge") from e
        raise
    except urllib.error.URLError as e:
        # Baker County serves its TLS leaf without the intermediate, so every verifying
        # client fails while browsers paper over it by fetching the issuer themselves. Named
        # explicitly so it reads as the county's misconfiguration rather than a dead host.
        if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            raise Refused(f"{url}: TLS chain incomplete (server omits its intermediate)") from e
        raise


def snapshot(url: str, dest: pathlib.Path, refetch: bool = False) -> tuple[bytes, bool]:
    """Fetch to `dest` unless it already exists. Returns (bytes, fresh).

    `fresh` is what source_dates() needs to decide whether `retrieved` may advance. Getting
    this wrong is not cosmetic: stamping the wall clock on a cached run moved `retrieved`
    forward every time the ingester ran, so the older a snapshot got, the fresher it claimed
    to be — which is precisely backwards for the one field a reviewer uses to judge staleness.
    """
    if dest.is_file() and not refetch:
        return dest.read_bytes(), False
    body, _ = get(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return body, True


def sniff(body: bytes, declared: str | None = None) -> str:
    """Format from MAGIC BYTES, never from the URL suffix or the server's say-so.

    oregon-audits learned this over 242 reports: 239 of its sources are an HTML viewer with
    a base64 PDF inside, 2 are plain PDFs at a .pdf URL, and one URL shape serves neither.
    County portals are worse — extensionless URLs that serve PDFs, .aspx that serves HTML,
    and vendor endpoints that serve JSON. Trusting the suffix converts HTML-to-text over PDF
    bytes and reports the source as CHANGED on every single run, forever.
    """
    if body.startswith(b"%PDF"):
        return "pdf"
    head = body[:512].lstrip()
    if head.startswith(b"{") or head.startswith(b"["):
        return "json"
    if head[:5].lower() == b"<?xml":
        return "xml"
    if b"<html" in head.lower() or b"<!doctype html" in head.lower():
        return "html"
    return (declared or "html")


def recorded_retrieved(doc_path: pathlib.Path) -> str | None:
    """The `retrieved:` already published for this document, so it can be carried forward."""
    if not doc_path.is_file():
        return None
    from corpus_toolkit.repo import parse_frontmatter
    fm, _ = parse_frontmatter(doc_path)   # takes a Path, not the text
    value = (fm or {}).get("retrieved")
    return str(value) if value else None


def source_dates(snap: pathlib.Path, fresh: bool, doc_path: pathlib.Path) -> tuple[str, str]:
    """(as_of, retrieved) — from the SOURCE, never from the wall clock.

    `retrieved` advances only when bytes were actually fetched; otherwise the published date
    is carried forward, falling back to the snapshot's mtime for a document that does not
    exist yet.

    `as_of` tracks `retrieved` here. Unlike eCFR, no county pins a date in its URL — the file
    at that address is whatever is there today, so the date we pulled it is genuinely the
    best available statement of what the text is as of. Inventing more precision than that
    would be a fabricated effective date on a legal instrument.
    """
    if fresh:
        retrieved = time.strftime("%Y-%m-%d")
    else:
        retrieved = (recorded_retrieved(doc_path)
                     or time.strftime("%Y-%m-%d", time.localtime(snap.stat().st_mtime)))
    return retrieved, retrieved


# Filenames that are drafts sitting beside adopted text in the same directory. Measured in
# five counties: Lane (APM `...Issue2REDLINE.pdf` next to `...CURRENT.pdf`), Clackamas
# (`zdoproposed`), Lincoln, Baker (`-DRAFT`), Gilliam (a redline employee handbook NEWER and
# LARGER than the adopted one, so "take the most recent" is actively wrong here).
# Enforced again in check_guardrails.py — publishing a draft as adopted law is the worst
# single error this corpus can make.
DRAFT_PATTERNS = (r"redline", r"\bissue\s*\d+\b", r"zdoproposed", r"-draft\b", r"\bdraft\b",
                  r"\bproposed\b")


def looks_like_draft(name: str) -> bool:
    import re
    return any(re.search(p, name, re.I) for p in DRAFT_PATTERNS)
