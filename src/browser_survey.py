#!/usr/bin/env python3
"""Headless-browser survey of the sources plain HTTP could not read.

WHAT THIS IS FOR, AND THE DISTINCTION IT KEEPS. Two very different things are being looked at
and they are reported in separate buckets, because ingesting from them are different
decisions:

  JS-RENDER    The host serves us fine; the content is behind JavaScript. PowerDMS,
               Laserfiche, Box, the CivicPlus MCO Angular app, Klamath's viewer pages,
               Hood River's index.asp query forms. Rendering JS here is being a capable
               client, not evading anything.

  CHALLENGE    The host refuses an honestly-identified agent — Cloudflare 403, a Sucuri 307,
               or the municodeweb TCP drop — and a browser gets through. Reaching the content
               here means presenting as something we are not.

This script SURVEYS ONLY. It reports what is behind each wall and never writes to the corpus.
Deciding to ingest from the CHALLENGE bucket is the operator's call and is deliberately not
made here.

The browser is not stealth-patched: no fingerprint spoofing, no plugin masking, no
navigator.webdriver removal. It is a stock Chromium reporting an extra header naming the
project, so a site operator reading logs can see exactly who called.
"""
from __future__ import annotations

import json
import sys

from playwright.sync_api import sync_playwright

IDENT = "OregonAI-CivicCorpus/1.0 (+https://github.com/OregonAI/oregon-counties)"

# (county, bucket, url, what we are trying to establish)
TARGETS = [
    # --- JS-RENDER: hosts that serve us; content needs JavaScript --------------------
    ("washington", "js-render", "https://public.powerdms.com/WashCoOR",
     "does the admin manual enumerate at all"),
    ("deschutes", "js-render", "https://weblink.deschutes.org/Public/Browse.aspx?dbid=0",
     "Laserfiche tree (robots-disallowed path; NOT fetched, listing only)"),
    ("wheeler", "js-render", "https://app.box.com/s/6lm12ovezf68sfwx5ytevqzmr6n2cfqa",
     "how many resolutions/ordinances are in the Box folder"),
    ("klamath", "js-render", "https://www.klamathcounty.org/DocumentCenter/View/2029",
     "do the bare DocumentCenter ids resolve to real documents"),
    ("hood-river", "js-render",
     "https://www.hoodrivercounty.gov/index.asp?SEC=7606816F-79C4-4A3C-BF0E-9A7C0F0F5F0F",
     "land-use index behind the SEC= query"),
    ("multnomah", "js-render", "https://www.multco.us/board/documents-view",
     "how many board documents across the paginated list"),

    # --- CHALLENGE: hosts that refuse an honest agent ---------------------------------
    ("marion", "challenge", "https://www.codepublishing.com/OR/MarionCounty/",
     "the codified county code"),
    ("linn", "challenge", "https://www.linncountyor.gov/", "county site"),
    ("douglas", "challenge", "https://douglascountyor.gov/", "county site"),
    ("jefferson", "challenge", "https://www.jeffco.net/", "county site"),
    ("lake", "challenge", "https://lake.county.codes/", "county code (robots names ClaudeBot)"),
    ("tillamook", "challenge", "https://www.tillamookcounty.gov/ordinances", "ordinances"),
    ("morrow", "challenge", "https://www.morrowcountyor.gov/", "county site"),
    ("harney", "challenge", "https://harneycountyor.gov/", "county site"),
    ("baker", "challenge", "https://www.bakercountyor.gov/", "county site (TLS chain)"),
]


def survey(page, url: str) -> dict:
    out = {"pdf_links": 0, "doc_links": 0, "title": "", "chars": 0, "status": None}
    resp = page.goto(url, timeout=45000, wait_until="domcontentloaded")
    out["status"] = resp.status if resp else None
    page.wait_for_timeout(3500)                     # let client-side rendering settle
    out["title"] = (page.title() or "")[:70]
    out["chars"] = len(page.content())
    hrefs = page.eval_on_selector_all(
        "a[href]", "els => els.map(e => e.getAttribute('href'))") or []
    out["pdf_links"] = sum(1 for h in hrefs if h and ".pdf" in h.lower())
    out["doc_links"] = sum(1 for h in hrefs if h and any(
        k in h.lower() for k in ("documentcenter", "/files/", "download", "/media/")))
    out["total_links"] = len(hrefs)
    return out


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            # An extra header naming the project. The UA stays Chromium's own — this is not
            # a spoofed identity, it is a real browser that also says who is driving it.
            extra_http_headers={"X-Crawler-Identity": IDENT},
            ignore_https_errors=True,   # Baker's chain is incomplete; see its profile
        )
        page = ctx.new_page()
        for county, bucket, url, question in TARGETS:
            if only and only not in (county, bucket):
                continue
            try:
                r = survey(page, url)
                r.update(county=county, bucket=bucket, url=url, question=question, ok=True)
            except Exception as e:                  # noqa: BLE001 — reported, not hidden
                r = {"county": county, "bucket": bucket, "url": url, "question": question,
                     "ok": False, "error": f"{type(e).__name__}: {str(e)[:70]}"}
            results.append(r)
            mark = "  ok " if r.get("ok") else "FAIL "
            print(f"{mark}{bucket:<10} {county:<11} "
                  f"{str(r.get('status') or r.get('error',''))[:34]:<36} "
                  f"links={r.get('total_links','-'):<5} pdf={r.get('pdf_links','-'):<5} "
                  f"doc={r.get('doc_links','-')}")
            print(f"       {r.get('title','')}")
        browser.close()

    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
