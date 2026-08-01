"""Washington County — Municode, and the county that prompted this corpus's one contested
decision.

611,272 people, 2nd largest, home rule charter, Board of Commissioners.

**THE ACCESS DECISION, IN FULL, BECAUSE THIS IS WHERE IT BITES.**

`library.municode.com` serves `User-agent: ClaudeBot` / `Disallow: /` plus
`Content-Signal: search=yes, ai-train=no, use=reference`. Washington County's Code of
Ordinances and Community Development Code both live there, and Washington is #2 by
population, so build order reaches this at position two and cannot defer it.

The operator's decision (PLAN.md Phase 12) is to ingest: the text of county law is authored
by the county, and Municode hosts it rather than writing it. What this corpus does NOT do is
disguise itself to get there. `src/fetch.py` sends an honest, self-identifying User-Agent,
and **api.municode.com serves it HTTP 200** — verified before a line of this profile was
written. So no impersonation is required and none is used. Compare `src/profiles/marion.py`,
where the honest agent IS refused and the county is therefore recorded `unavailable` rather
than fetched under a browser disguise.

The determination is recorded per host in `crawl` below, including the Content-Signal string
verbatim, so a reviewer sees exactly what was decided and against what.

**THE ROUTE.** The library.municode.com page a human visits is a JavaScript shell. The API
behind it is open and needs three calls in order — ClientContent for the products,
Jobs/latest for the current supplement's jobId, then codesToc, which 404s without a real
jobId. One document per top-level Title, because CodesContent on a Title returns every
section beneath it in one response.

**TWO SEPARATE CODE BOOKS**, which is unusual and is the reason for two families here rather
than one: the Code of Ordinances (productId 16681) and the Community Development Code
(productId 15510) are distinct Municode products, and the CDC is the land-use instrument
that ORS 197 and the OAR 660 statewide planning goals bind.

Verified 2026-07-31: clientId 11326; Code of Ordinances 16681 (supplement 25, jobId 436713,
20 top-level nodes); Community Development Code 15510. Honest User-Agent, HTTP 200.
"""
from __future__ import annotations

import json
import re

# Municode returns section text as HTML fragments inside JSON. Tags are stripped here rather
# than by extract_html, because the payload is an API response and not a page: html_to_text
# on the raw JSON would render the field names and punctuation as if they were prose.
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t ]+")


def extract(raw: bytes, fmt: str, src: dict) -> tuple[str, dict]:
    """Municode CodesContent JSON -> the text of one Title and all its sections.

    Headings are emitted as `### ` and never `## `. A line beginning `## ` at column zero
    terminates `## Full text` for corpus_toolkit.repo.FULLTEXT_RE, silently discarding
    everything after it — measured at 1 character of 632,927 in federal-reference. `###`
    does not match the lookahead.
    """
    from src.extract import guard_headings

    docs = json.loads(raw).get("Docs") or []
    out: list[str] = []
    for doc in docs:
        title = (doc.get("Title") or "").strip()
        if title:
            out.append(f"### {title}")
        body = _TAG.sub(" ", doc.get("Content") or "")
        body = _WS.sub(" ", __import__("html").unescape(body))
        body = "\n".join(ln.strip() for ln in body.splitlines() if ln.strip())
        if body:
            out.append(body)
    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(out)).strip()
    return guard_headings(text), {"sections": len(docs)}


PROFILE = {
    "slug": "washington",
    "name": "Washington",
    "discovery": "municode-api",
    "site": "https://www.washingtoncountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "library.municode.com names ClaudeBot and disallows it, and sets "
            "Content-Signal: ai-train=no. The operator's decision (PLAN.md Phase 12) is that "
            "the text of county law is authored by the county and the vendor is a host, so "
            "this directive is not treated as binding for that text. The line held: we do "
            "not evade technical access controls. api.municode.com serves HTTP 200 to the "
            "honest, self-identifying User-Agent in src/fetch.py, so nothing here "
            "impersonates a browser. Fetched once, cached, rate-limited."),
        "hosts": [
            {"host": "library.municode.com",
             "robots_url": "https://library.municode.com/robots.txt",
             "ai_block": True,
             "content_signal": "search=yes, ai-train=no, use=reference",
             "notes": "Cloudflare-managed AI block naming ClaudeBot, CCBot, GPTBot, "
                      "Amazonbot, Applebot-Extended, Bytespider and Google-Extended, each "
                      "with Disallow: /. Framed as an EU DSM Art. 4 rights reservation. "
                      "This host is the human-facing JS shell and is NOT fetched by this "
                      "profile; the API below is."},
            {"host": "api.municode.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Open JSON API, no robots.txt served. Returns 200 to the honest agent."},
            {"host": "www.washingtoncountyor.gov",
             "robots_url": "https://www.washingtoncountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Stock Drupal, byte-identical to Multnomah's. No AI agent named."},
        ],
    },
    "upstream_signal": (
        "Jobs/latest/<productId> names the current supplement and its publish date, so the "
        "supplement number is a real change signal — the only vendor in this build that "
        "exposes one."),
    "families": {
        "code": {
            "discovery": "municode-api",
            "client_id": 11326,
            "product_id": 16681,          # Code of Ordinances
            "format": "json",
            # The supplement history table is a publication log, not law.
            "skip_re": r"SUPPLEMENT HISTORY",
        },
        "land-use": {
            "discovery": "municode-api",
            "client_id": 11326,
            "product_id": 15510,          # Community Development Code — a SEPARATE book
            "format": "json",
            "skip_re": r"SUPPLEMENT HISTORY",
        },
        "orders": {
            "skip": (
                "Land use ordinances as raw enactments are on the county's own site at "
                "/lut/land-use-ordinances rather than in Municode. Reachable and not "
                "blocked; deferred to keep this pass to the two code books."),
        },
        # RESOLVED 2026-08-01 with a rendered browser, and the answer was neither of the
        # two possibilities this note used to offer. The portal is GONE:
        #
        #   public.powerdms.com/WashCoOR          renders "No Site Found"
        #   public.powerdms.com/washcoor/documents  404 {"code":"key_not_found"}
        #
        # Plain HTTP had returned 200 with the literal body "PowerDMS", which is the app
        # shell it serves for any path — so "200" said nothing about whether the site
        # existed. Only rendering it distinguished a wall from a dead link.
        #
        # So Washington's administrative manual is not behind an access barrier and is not
        # an absence at the county: the survey's recorded location no longer exists. Where
        # the county publishes it now was not established, and that is the honest state.
        "policies": {
            "skip": (
                "The PowerDMS portal recorded by the survey NO LONGER EXISTS — "
                "public.powerdms.com/WashCoOR renders 'No Site Found' and the API returns "
                "key_not_found, confirmed with a rendered browser on 2026-08-01. Plain HTTP "
                "returned 200 with the app shell, which is why this looked like a wall. "
                "Where Washington publishes its Administrative Manual now is NOT "
                "established; this is neither a block nor an absence at the county."),
        },
    },
}
