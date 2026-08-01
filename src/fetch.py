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

HTTP/2, AND WHY THAT TURNED OUT TO MATTER MORE THAN ANY OF THE ABOVE. Marion County's code
was recorded `unavailable` for four tranches on the belief that Cloudflare was refusing our
identity. It was not. With the SAME User-Agent and the same headers:

    curl --http2    -> 200
    curl --http1.1  -> 403

Python's urllib speaks only HTTP/1.1, so every request this module made was scored on
protocol version and refused. The block was never about who we said we were.

That is worth stating plainly because the wrong diagnosis pointed at the wrong remedy: it
framed a solvable client-modernity problem as a choice between disguising ourselves and
giving up, and a headless browser was reached for before a protocol check. Speaking HTTP/2
is not impersonation — it is being a current client, with the honest User-Agent unchanged.
"""
from __future__ import annotations

import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import httpx

USER_AGENT = ("OregonAI-CivicCorpus/1.0 "
              "(+https://github.com/OregonAI/oregon-counties; public-records archival)")

HEADERS = {"User-Agent": USER_AGENT,
           "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9",
           "Connection": "close"}

TIMEOUT = 120
MIN_INTERVAL = 2.0          # seconds between requests to the SAME host

# Escalating waits after a 429. Ends rather than looping forever, so a host that genuinely
# will not serve us produces a recorded refusal instead of an ingest that never finishes.
BACKOFF = (5, 15, 45)


def _retry_after(headers) -> float | None:
    """Honour `Retry-After` when the host states one — it knows better than our guess."""
    raw = (headers or {}).get("Retry-After")
    try:
        return max(1.0, min(120.0, float(raw)))
    except (TypeError, ValueError):
        return None


_last: dict[str, float] = {}
_shared: httpx.Client | None = None


def _client() -> httpx.Client:
    """One HTTP/2 client, reused. Redirects followed; TLS still verified."""
    global _shared
    if _shared is None:
        _shared = httpx.Client(http2=True, follow_redirects=True, timeout=TIMEOUT,
                               limits=httpx.Limits(max_connections=4))
    return _shared


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


def get(url: str, _attempt: int = 0) -> tuple[bytes, str]:
    """Fetch once, honestly, over HTTP/2. Returns (body, content_type).

    Raises Refused/Challenge — see the module docstring for why those are kept distinct from
    a 404, and from each other.
    """
    _throttle(url)
    try:
        resp = _client().get(url, headers=HEADERS)
    except httpx.ConnectError as e:
        # Baker County serves its TLS leaf without the intermediate, so every verifying
        # client fails while browsers paper over it. Named so it reads as the county's
        # misconfiguration rather than a dead host.
        if "CERTIFICATE_VERIFY" in str(e).upper():
            raise Refused(f"{url}: TLS chain incomplete "
                          f"(server omits its intermediate)") from e
        raise
    except httpx.RemoteProtocolError as e:
        # lb2.municodeweb.com completes TLS and then drops the connection rather than
        # answering — a refusal delivered as a reset instead of a status code.
        raise Refused(f"{url}: connection closed without a response ({e})") from e

    code = resp.status_code
    if code == 429 and _attempt < len(BACKOFF):
        # 429 IS NOT A REFUSAL. It means "you are going too fast" — a request to slow down,
        # not a decision to exclude us. Coos returned it on four documents at a 2s interval.
        wait = _retry_after(resp.headers) or BACKOFF[_attempt]
        print(f"    429 from {urllib.parse.urlsplit(url).netloc} — backing off {wait}s "
              f"(attempt {_attempt + 1}/{len(BACKOFF)})")
        time.sleep(wait)
        return get(url, _attempt + 1)
    if code in (401, 403, 429):
        mitigated = resp.headers.get("cf-mitigated", "")
        raise (Challenge if mitigated == "challenge" else Refused)(
            f"{url}: HTTP {code}"
            f"{' (Cloudflare managed challenge)' if mitigated else ''}")
    if code == 307 and not resp.headers.get("Location"):
        raise Challenge(f"{url}: 307 with no Location — bot challenge")
    resp.raise_for_status()
    return resp.content, (resp.headers.get("Content-Type") or "").split(";")[0].strip()


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
    # Office documents. `\xd0\xcf\x11\xe0` is the OLE compound-file header (.doc/.xls);
    # a ZIP magic with `word/` or `[Content_Types]` inside is OOXML (.docx/.xlsx).
    #
    # These MUST be detected rather than left to the declared format, because the fallback
    # below trusts the manifest — and a .doc handed to the PDF extractor raises
    # `PdfStreamError: Stream has ended unexpectedly`, which reads like a corrupt download
    # rather than a file we simply cannot parse. Sherman publishes its permit APPLICATION
    # FORMS as .doc alongside its land-use PDFs; six of them failed that way.
    if body.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "doc"
    if body.startswith(b"PK\x03\x04") and (b"word/" in body[:4000]
                                            or b"[Content_Types]" in body[:4000]):
        return "docx"
    if b"<html" in head.lower() or b"<!doctype html" in head.lower():
        return "html"
    # The declared format is the LAST resort, not the first. Trusting it over the bytes is
    # how a PDF served from an extensionless URL gets HTML-to-text run over it and reports
    # CHANGED on every run forever — and how a .doc reaches the PDF parser.
    return (declared or "html")


# Formats this corpus has no extractor for. Reported by name rather than attempted, so the
# log says "we cannot read this" instead of raising a parser error that reads like a corrupt
# download. These are overwhelmingly application forms rather than law.
UNSUPPORTED = {"doc", "docx", "xls", "xlsx"}


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


# Filenames that are DRAFTS sitting beside adopted text in the same directory. Measured in
# five counties: Lane (APM `...Issue2REDLINE.pdf` next to `...CURRENT.pdf`), Clackamas
# (`zdoproposed`), Lincoln, Baker (`-DRAFT`), Gilliam (a redline employee handbook NEWER and
# LARGER than the adopted one, so "take the most recent" is actively wrong here).
#
# `draft`/`proposed` ARE ONLY DRAFT MARKERS IN A VERSION POSITION — at the start or end of a
# name, or delimited — never mid-sentence. Multnomah adopts resolutions ABOUT proposals:
# "Resolution Referring Charter Review Committee Proposed Amendments To The Voters" and
# "Resolution Adopting ... For Inclusion In The Draft Environmental Impact Statement" are
# adopted law whose SUBJECT is a proposal. A bare \bproposed\b flagged 17 such documents as
# drafts. The word describes what the instrument is about; the position tells you whether it
# describes the instrument.
DRAFT_PATTERNS = (
    r"redline",                      # unambiguous wherever it appears
    r"\bissue\s*\d+\b",             # Lane's APM revision markers
    r"zdoproposed",                  # Clackamas' proposed-amendment pages
    # Trailing version marker. The optional extension group matters: without it
    # `employee-handbook-DRAFT.pdf` slips through, because `.pdf` sits between the marker
    # and the end of the string.
    r"[-_.(\[]\s*(?:draft|proposed)\s*[-_.)\]]*\s*(?:\.[a-z0-9]{2,4})?$",
    r"^\s*(?:draft|proposed)\s*[-_.]",                   # leading version marker
)


def looks_like_draft(name: str) -> bool:
    import re
    return any(re.search(p, name, re.I) for p in DRAFT_PATTERNS)
