#!/usr/bin/env python3
"""Discover and ingest Oregon county policy instruments.

TWO PHASES, WITH A HUMAN GATE BETWEEN THEM — the platform's stated workflow:

    python3 src/ingest_counties.py --discover lane   # write _meta/sources/lane.yml
    <a person reads the source list in a PR>          # GATE
    python3 src/ingest_counties.py --only lane        # fetch, extract, write documents

Discovery is separated because it is the step that decides WHAT IS LAW. A regex that quietly
matches a draft, or misses half a code, produces a corpus that looks complete and is not, and
that judgement is not one an ingester should make unreviewed. The gate is the reason
`sources:` is committed rather than computed at ingest time.

DISCOVERY MODES exist one per shape the 36-county survey actually found. They are not
invented ahead of need: a mode with no county using it is untested code that reads as
capability.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from corpus_toolkit import config as config_mod          # noqa: E402
from corpus_toolkit.documents import write_document      # noqa: E402
from corpus_toolkit.sources.snapshots import record_snapshot  # noqa: E402
from src import extract, fetch                           # noqa: E402
from src.profiles import load_profiles                   # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_meta" / "sources"
SNAPSHOTS = ROOT / "_meta" / "snapshots"
COUNTIES = ROOT / "counties"

FAMILY_DOCTYPE = {"code": "ordinance", "orders": "ordinance",
                  "policies": "policy", "land-use": "ordinance"}
FAMILY_AUTHORITY = {"code": "county_ordinance", "orders": "county_ordinance",
                    "policies": "county_policy", "land-use": "county_ordinance"}


# ------------------------------------------------------------------ discovery modes

def discover_link_list(profile: dict, family: str, cfg: dict) -> list[dict]:
    """Fetch a listing page, pull document links out of it, resolve them.

    Used by the counties that publish an HTML index of PDFs — the most common shape by far
    (12 of 36 self-host PDFs). `link_re` must have one capturing group holding the href.

    Curry County is why hrefs are re-resolved rather than string-joined: it writes
    `href= "..."` with a space and resolves bare filenames against a root <base> tag, so a
    strict regex silently drops every document and produces a false none-found.
    """
    # A family of one or two known documents does not need discovery, and forcing it through
    # a regex produces worse metadata than stating it: Polk's records policy is linked as
    # `/DocumentCenter/View/3546` with no name segment at all, so a discovered title would be
    # the string "3546". Declaring it is both more honest and more useful.
    if cfg.get("explicit"):
        return [dict(item) for item in cfg["explicit"]]

    listings = _listing_urls(cfg)
    link_re = re.compile(cfg["link_re"], re.I)
    seen, out = set(), []
    for listing in listings:
        _scrape(listing, cfg, link_re, seen, out)

    if cfg.get("dedupe") == "name-highest-id":
        # CivicPlus re-uploads a replaced document under a NEW DocumentCenter id while
        # keeping the old one linked, so the same instrument appears twice under one name —
        # Yamhill has two `ORD638-PDF` links, ids 17344 and 17563. Keeping both would put two
        # documents in the corpus each claiming to be Ordinance 638, with nothing telling a
        # reader which is the law. Highest id wins: DocumentCenter ids increase monotonically,
        # so the larger one is the later upload.
        best: dict[str, tuple[int, dict]] = {}
        for item in out:
            m = re.search(r"/(\d+)/", item["url"])
            n = int(m.group(1)) if m else 0
            key = item["name"].lower()
            if key not in best or n > best[key][0]:
                best[key] = (n, item)
        dropped = len(out) - len(best)
        if dropped:
            print(f"    deduped {dropped} superseded upload(s) by DocumentCenter id")
        out = [v[1] for v in best.values()]
    return out


def _listing_urls(cfg: dict) -> list[str]:
    """The page(s) to scrape.

    THREE FORMS, because counties organise indexes three ways and a single `listing_url`
    only covers the first:

        listing_url                one page holding every link          (Multnomah, Lane)
        listing_urls: [...]        several pages, named explicitly
        index_url + index_re       an index of listing pages, walked    (Polk: /540 lists
                                   nine Title pages, each holding the actual PDFs)

    Without the third, Polk's code discovers exactly one document — the single PDF that
    happens to be linked from the index itself — and reports success. That is the shape of
    silent under-collection this whole pipeline keeps having to defend against.
    """
    if cfg.get("listing_urls"):
        return list(cfg["listing_urls"])
    if not cfg.get("index_url"):
        return [cfg["listing_url"]]

    body, _ = fetch.get(cfg["index_url"])
    page = body.decode("utf-8", "replace")
    found, seen = [], set()
    for m in re.finditer(cfg["index_re"], page, re.I):
        u = _encode(urllib.parse.urljoin(cfg["index_url"], html.unescape(m.group(1).strip())))
        if u not in seen:
            seen.add(u)
            found.append(u)
    if not found:
        raise ValueError(f"index_re matched nothing on {cfg['index_url']} — the index "
                         f"changed shape, and scraping zero pages would look like success")
    return found


def _scrape(listing: str, cfg: dict, link_re, seen: set, out: list) -> None:
    body, _ = fetch.get(listing)
    # NOT named `html` — that shadows the stdlib module this function needs for unescape().
    page = body.decode("utf-8", "replace")
    base = cfg.get("base_url") or listing
    m = re.search(r'<base[^>]+href\s*=\s*["\']([^"\']+)', page, re.I)
    if m:
        base = urllib.parse.urljoin(listing, m.group(1))

    for match in link_re.finditer(page):
        # An href is HTML, so entities in it are markup, not data. Multnomah publishes
        # `chapter_29a:_references_to_ors,_1990_code_&amp;_ordinances`, and resolving that
        # literally requests a path containing `&amp;` and gets a 404 — five Multnomah
        # documents, including a whole code chapter, were lost exactly this way.
        href = html.unescape(match.group(1).strip())
        url = _encode(urllib.parse.urljoin(base, href))
        # Dedupe on the PATH, ignoring the query. Publishers link the same file both plainly
        # and with a cache-busting `?t=<timestamp>`, and treating those as two documents
        # produces two records of one instrument — Wasco links its Title VI Plan both ways
        # on the same page. The first form seen wins, so a plain URL is preferred to one
        # carrying a timestamp that will change.
        key = urllib.parse.urlsplit(url)._replace(query="", fragment="").geturl()
        if key in seen:
            continue
        seen.add(key)
        name = _name_from_url(url)
        # A NAMELESS LINK GETS ITS NAME FROM THE SERVER. `/DocumentCenter/View/2029` yields
        # the bare id "2029", which is useless as an id and worse as a title; the server's
        # Content-Disposition says "Economic Development - 8-24-17.pdf". Only asked when the
        # derived name is purely numeric, so this costs one extra request per nameless link
        # rather than one per link.
        if cfg.get("resolve_names") and name.isdigit():
            name = fetch.filename_of(url) or name
        if fetch.looks_like_draft(name) or fetch.looks_like_draft(href):
            continue
        if cfg.get("exclude_re") and re.search(cfg["exclude_re"], url, re.I):
            continue
        out.append({"url": url, "name": name})


def discover_mco_s3(profile: dict, family: str, cfg: dict) -> list[dict]:
    """CivicPlus Municipal Code Online — enumerate the shared S3 bucket, not the SPA.

    The portal is an AngularJS app with no server-rendered HTML, but its backing bucket
    answers unauthenticated ListObjectsV2. Measured on Deschutes: 932 objects, 907 PDFs,
    ordinances back to 1980, filenames carrying the recording date. The bucket is SHARED —
    462 client prefixes — so this works for any MCO county.

    A bare prefix path 404s; only the `?list-type=2&prefix=` query answers.
    """
    bucket = cfg.get("bucket", "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new")
    prefix = cfg["prefix"]
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    token, out = None, []
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        body, _ = fetch.get(f"{bucket}?{urllib.parse.urlencode(q)}")
        root = ET.fromstring(body)
        for c in root.findall("s3:Contents", ns):
            key = c.findtext("s3:Key", "", ns)
            if not key.lower().endswith(".pdf"):
                continue
            name = urllib.parse.unquote(key.rsplit("/", 1)[-1])
            if fetch.looks_like_draft(name):
                continue
            if cfg.get("key_re") and not re.search(cfg["key_re"], key, re.I):
                continue
            out.append({"url": f"{bucket}/{urllib.parse.quote(key)}", "name": name,
                        "size": int(c.findtext("s3:Size", "0", ns))})
        token = root.findtext("s3:NextContinuationToken", None, ns)
        if not token:
            break
        token = urllib.parse.unquote(token)
    return out


MUNICODE = "https://api.municode.com"


def discover_municode(profile: dict, family: str, cfg: dict) -> list[dict]:
    """Municode — the JSON API, which is open while the HTML library index is a JS shell.

    THREE ENDPOINTS, IN THIS ORDER, and getting the order wrong is why the first version of
    this function returned nothing:

        ClientContent/<clientId>          the products this client publishes
        Jobs/latest/<productId>           the current supplement -> the jobId everything needs
        codesToc?jobId=&productId=        the table of contents; 404s WITHOUT a real jobId
        CodesContent?jobId=&nodeId=&...   the text of one node and all its descendants

    A CORRECTION TO WHAT THIS DOCSTRING USED TO SAY. It claimed `Jobs/latest/<id>` returns
    204 for every Oregon client and therefore tests nothing. That is wrong: for Washington
    County's Code of Ordinances (productId 16681) it returns supplement 25 with jobId 436713,
    and without that jobId `codesToc` 404s. The 204 observation was made against a CLIENT id
    where this endpoint takes a PRODUCT id.

    `latestUpdatedDate: null` still means an empty shell rather than a code — Lincoln County
    has exactly that, and recording it as a source would have been a fabricated one.

    One source per TOP-LEVEL TOC NODE (a Title), because CodesContent on a title returns that
    title and every section under it in one response. Per-section would be ~95 requests per
    title for text we already hold.
    """
    body, _ = fetch.get(f"{MUNICODE}/ClientContent/{cfg['client_id']}")
    out = []
    for code in json.loads(body).get("codes", []):
        pid = code.get("productId")
        if cfg.get("product_id") and pid != cfg["product_id"]:
            continue
        if not code.get("latestUpdatedDate"):
            continue                       # an empty shell, not a code
        job, _ = fetch.get(f"{MUNICODE}/Jobs/latest/{pid}")
        job_id = json.loads(job).get("Id")
        toc, _ = fetch.get(f"{MUNICODE}/codesToc?jobId={job_id}&productId={pid}")
        for node in json.loads(toc).get("Children") or []:
            node_id, heading = node.get("Id"), (node.get("Heading") or "").strip()
            if not node_id or cfg.get("skip_re") and re.search(cfg["skip_re"], heading, re.I):
                continue
            out.append({
                "url": (f"{MUNICODE}/CodesContent?jobId={job_id}"
                        f"&nodeId={urllib.parse.quote(node_id)}&productId={pid}"),
                "name": node_id,
                "title": heading,
                "id": f"{profile['slug']}-{family}-{node_id.lower()}",
            })
    return out


def discover_ecode360(profile: dict, family: str, cfg: dict) -> list[dict]:
    """General Code's eCode360 — parse the table of contents embedded in the landing page.

    There is no JSON API (`/api/toc/<code>` 404s), but the TOC is present in the HTML as
    HTML-escaped JSON, one object per node:

        {"prefix":"Ttl 1","tocName":"General Provisions","guid":"44303313",
         "href":"/44303313","title":"General Provisions","number":"1", ...}

    So the readable identity IS available and there is no need to fall back on the opaque
    guid: a document lands as `clatsop-code-ttl-1-general-provisions` rather than
    `clatsop-code-44303313`, which is the difference between an id a citation can reach and
    a number nobody can.

    ONE DOCUMENT PER TITLE, matching the Municode route and for the same reason — a node
    page carries its whole subtree, so per-section would be hundreds of requests for text
    already in hand.

    General Code is the largest commercial code vendor among Oregon counties (4 of 36, ahead
    of Municode's 3), so this mode is worth its length: it serves Clatsop and Crook now and
    Lake when that county is reached.
    """
    body, _ = fetch.get(cfg["toc_url"])
    page = html.unescape(body.decode("utf-8", "replace"))
    prefix_re = cfg.get("prefix_re", r"Ttl[^\"]*")

    out, seen = [], set()
    for m in re.finditer(
            rf'\{{"prefix":"({prefix_re})","tocName":"([^"]*)","guid":"(\d+)"', page):
        pref, name, guid = (s.strip() for s in m.groups())
        if guid in seen:
            continue
        seen.add(guid)
        # "(Reserved)" titles are placeholders holding a number against future use. They are
        # real TOC entries and contain no law; ingesting them would pad the count with
        # documents whose entire content is the word Reserved.
        if re.fullmatch(r"\(?reserved\)?", name, re.I):
            continue
        slug = _slugify(f"{pref} {name}")
        out.append({
            "url": f"{cfg.get('base', 'https://ecode360.com')}/{guid}",
            "name": slug,
            "title": f"{pref}: {name}",
            "id": f"{profile['slug']}-{family}-{slug}",
        })
    if not out:
        raise ValueError(f"{cfg['toc_url']}: no TOC nodes matched — eCode360 changed its "
                         f"page shape, and returning nothing would look like an empty code")
    return out


def discover_js(profile: dict, family: str, cfg: dict) -> list[dict]:
    """Render a page with a real browser, then read its links.

    FOR HOSTS THAT SERVE US AND SIMPLY NEED JAVASCRIPT — not for hosts that refuse us.
    Multnomah's board-documents list is the measured case: plain HTTP returns ZERO file links
    across pages 0, 1 and 23, while a rendered page yields 29 on page one. The content is
    public, the server answers our honest agent 200, and the only obstacle is that the list is
    built client-side. Rendering it is being a capable client.

    The distinction this mode does NOT cross: it is never pointed at a host that refused an
    honestly-identified request. Those are recorded `unavailable` in their profiles and
    reaching them would mean presenting as something we are not, which is a different act and
    a decision that is not this function's to make.

    An `X-Crawler-Identity` header names the project on every request, so a site operator
    reading logs sees who called even though the User-Agent is Chromium's own.

    `pages` gives a printf-style URL template and a count for paginated lists.
    """
    from playwright.sync_api import sync_playwright

    urls = ([cfg["url_template"] % n for n in range(cfg["pages"])]
            if cfg.get("pages") else _listing_urls(cfg))
    pattern = re.compile(cfg["link_re"], re.I)
    seen, out = set(), []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(extra_http_headers={
            "X-Crawler-Identity": fetch.USER_AGENT})
        page = ctx.new_page()
        for i, u in enumerate(urls, 1):
            try:
                page.goto(u, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(cfg.get("settle_ms", 2500))
                hrefs = page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => e.getAttribute('href'))") or []
            except Exception as e:                 # noqa: BLE001 — reported, not hidden
                print(f"    page {i}/{len(urls)} FAILED: {type(e).__name__}: {str(e)[:60]}")
                continue
            before = len(out)
            for href in hrefs:
                if not href or not pattern.search(href):
                    continue
                url = _encode(urllib.parse.urljoin(u, html.unescape(href.strip())))
                key = urllib.parse.urlsplit(url)._replace(query="", fragment="").geturl()
                if key in seen:
                    continue
                seen.add(key)
                name = _name_from_url(url)
                if fetch.looks_like_draft(name) or fetch.looks_like_draft(href):
                    continue
                if cfg.get("exclude_re") and re.search(cfg["exclude_re"], url, re.I):
                    continue
                out.append({"url": url, "name": name})
            if len(urls) > 3:
                print(f"    page {i}/{len(urls)}: +{len(out) - before} (total {len(out)})")
        browser.close()

    if not out:
        raise ValueError(f"rendered {len(urls)} page(s) and matched nothing — the page shape "
                         f"changed, and returning nothing would look like an empty family")
    return out


DISCOVERY = {
    "link-list": discover_link_list,
    "js-render": discover_js,
    "mco-s3": discover_mco_s3,
    "municode-api": discover_municode,
    "ecode360": discover_ecode360,
}


# ------------------------------------------------------------------ discovery driver

def run_discovery(slug: str, profiles: dict) -> int:
    profile = profiles[slug]
    mode = profile["discovery"]
    group = {
        "group": slug,
        "title": f"{profile.get('name', slug.title())} County sources",
        "county": f"{slug}-county",
        "crawl": profile["crawl"],
        "last_checked": time.strftime("%Y-%m-%d"),
        "upstream_signal": profile.get("upstream_signal",
                                       "No change feed. Freshness is re-fetch and re-hash."),
        "sources": [],
    }
    custom = getattr(profile.get("_module"), "discover", None)

    for family, cfg in profile["families"].items():
        if cfg.get("skip"):
            print(f"  {family:<10} SKIPPED: {cfg.get('skip')}")
            continue
        fn = custom or DISCOVERY.get(cfg.get("discovery", mode))
        if fn is None:
            print(f"  {family:<10} ERROR: unknown discovery mode "
                  f"{cfg.get('discovery', mode)!r}", file=sys.stderr)
            return 1
        try:
            found = fn(profile, family, cfg)
        except fetch.Refused as e:
            # Refused is NOT a missing document. Recorded so the manifest says "we were
            # refused" rather than silently holding fewer sources than the county publishes.
            print(f"  {family:<10} REFUSED: {e}", file=sys.stderr)
            group["crawl"]["decision"] = "unavailable"
            continue
        for item in found:
            group["sources"].append({
                # A profile's own discover() may set `id` and `title` — it knows the
                # county's identifiers (an ordinance number, a code chapter) and the
                # generic slugifier only knows the filename. Filename-derived ids are the
                # fallback, not the rule: `1616608184_35-752-ordinance-no-80-201-recorded-9-18-1980`
                # is stable but says nothing, and a citation cannot be resolved to it.
                "id": item.get("id") or _fallback_id(slug, family, item["url"]),
                **({"_explicit_id": True} if item.get("id") else {}),
                "url": item["url"],
                "family": family,
                "format": cfg.get("format", "pdf"),
                "sha256": "",
                "title": item.get("title") or _titleize(item["name"]),
                "last_checked": time.strftime("%Y-%m-%d"),
            })
        print(f"  {family:<10} {len(found)} source(s)")

    # WIDEN COLLIDING IDS BEFORE DECIDING THEY ARE DUPLICATES. Filenames are not unique
    # across a document tree — Wasco files two different 1989 ordinances whose names agree
    # for the first 60 characters — and the parent directory is what actually distinguishes
    # them. Only the colliding ids are widened, so every other id stays short.
    from collections import Counter as _Counter
    counts = _Counter(s["id"] for s in group["sources"])
    for s in group["sources"]:
        if counts[s["id"]] > 1 and not s.get("_explicit_id"):
            s["id"] = _fallback_id(slug, s["family"], s["url"], widen=True)

    # STILL COLLIDING AFTER WIDENING means the names are genuinely the same, not truncated.
    # Multnomah adopts a "Resolution Establishing Fees for Building Permits..." most years
    # and files each under that same title; six share one slug at 130 characters. They are
    # DIFFERENT INSTRUMENTS, so deduplicating would delete law — the only correct move is a
    # stable discriminator. A short hash of the path is deterministic across runs, so an id
    # does not churn between ingests, and the readable part of the id is untouched.
    counts = _Counter(s["id"] for s in group["sources"])
    for s in group["sources"]:
        if counts[s["id"]] > 1 and not s.get("_explicit_id"):
            import hashlib
            path = urllib.parse.urlsplit(s["url"]).path
            s["id"] = f"{s['id']}-{hashlib.sha1(path.encode()).hexdigest()[:6]}"

    # IDS MUST BE UNIQUE, and this is checked here rather than at ingest because a collision
    # at ingest is INVISIBLE: two sources with one id write the same file, the second
    # silently overwrites the first, and the corpus ends up holding one document while the
    # manifest claims two. Discovery is the only place the whole set is in hand at once.
    dupes = {i: n for i, n in
             __import__("collections").Counter(s["id"] for s in group["sources"]).items()
             if n > 1}
    if dupes:
        print(f"\nABORT: {len(dupes)} duplicate source id(s) — nothing written.\n"
              f"Each would silently overwrite the last at ingest:", file=sys.stderr)
        for i, n in sorted(dupes.items(), key=lambda kv: -kv[1])[:8]:
            print(f"  {n}x  {i}", file=sys.stderr)
        return 1

    # `_explicit_id` is an internal marker for the widening pass above and must NOT reach
    # the manifest — the source-group schema is additionalProperties: false, so leaking it
    # fails validation for every source in the file. Dropped here rather than never set,
    # because the widening pass genuinely needs to know which ids a profile chose itself.
    for s in group["sources"]:
        s.pop("_explicit_id", None)

    SOURCES.mkdir(parents=True, exist_ok=True)
    out = SOURCES / f"{slug}.yml"
    out.write_text(yaml.safe_dump(group, sort_keys=False, allow_unicode=True, width=100),
                   encoding="utf-8")
    print(f"wrote {out}  ({len(group['sources'])} sources) — REVIEW BEFORE INGESTING")
    return 0


# Trailing path segments that are an ACTION rather than a name. Drupal serves documents as
# `/file/<real-name>/download`, so the last segment is the verb and the identifying part is
# the one before it. Taking the last segment blindly gave every Multnomah document the id
# `multnomah-code-download` — 20 sources colliding on one id, which the manifest happily
# recorded because nothing downstream checks id uniqueness at discovery time.
_ACTION_SEGMENTS = {"download", "view", "open", "file", "get", "inline", ""}


def _encode(url: str) -> str:
    """Percent-encode a URL path that came out of an href.

    Publishers write hrefs with literal spaces and other unencoded characters, and browsers
    fix them silently. urllib does not: `urlopen` on
    `.../Lane Code/LC16.245_249.pdf` raises `InvalidURL: URL can't contain control
    characters`. Lane serves 50 land-use PDFs from a directory with a space in its name, so
    this is not an edge case — it is most of a county.

    `safe` keeps the characters that are already structural, so a path that IS correctly
    encoded is not double-encoded into a 404.
    """
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        parts.scheme, parts.netloc,
        urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=~-._"),
        urllib.parse.quote(parts.query, safe="/%:@!$&'()*+,;=~-._?"),
        parts.fragment))


def _name_from_url(url: str) -> str:
    parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
    while parts and parts[-1].lower() in _ACTION_SEGMENTS:
        parts.pop()
    return urllib.parse.unquote(parts[-1]) if parts else "document"


def _fallback_id(slug: str, family: str, url: str, widen: bool = False) -> str:
    """`<county>-<family>-<filename>`, widened with the parent directory on a collision.

    Filenames are not unique across a document tree: Wasco files two different 1989
    ordinances whose names agree for the first 60 characters, and truncation made them one
    id. Rather than truncate harder or append an arbitrary counter, the parent directory —
    which is what actually distinguishes them — is folded in. Deterministic, and the id still
    says what the document is.
    """
    parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
    while parts and parts[-1].lower() in _ACTION_SEGMENTS:
        parts.pop()
    # 60 characters is plenty for a normal filename and NOT enough for a collision: Wasco
    # files two 1989 ordinances that agree for their first 60 characters and differ only in
    # the destination zone, so widening has to lengthen as well as add the directory.
    stem = _slugify(urllib.parse.unquote(parts[-1]), 130 if widen else 60) if parts else "document"
    if widen and len(parts) > 1:
        parent = _slugify(urllib.parse.unquote(parts[-2]))
        if parent and parent not in stem:
            stem = f"{parent}-{stem}"
    return f"{slug}-{family}-{stem}"


def _slugify(name: str, max_len: int = 60) -> str:
    stem = re.sub(r"\.[a-z0-9]{2,4}$", "", name, flags=re.I)
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")[:max_len]


def _titleize(name: str) -> str:
    # Names come out of href attributes, so HTML entities survive into them: Multnomah's
    # `chapter_29a:_references_to_ors,_1990_code_&amp;_ordinances` would otherwise publish a
    # title containing a literal `&amp;`.
    stem = html.unescape(re.sub(r"\.[a-z0-9]{2,4}$", "", name, flags=re.I))
    stem = stem.replace("_", " ").strip()
    # Title-case only when the source gave us no case information at all — a slug is
    # lowercase by construction, but a real filename's capitalisation is the publisher's and
    # is left alone.
    return stem.title() if stem == stem.lower() else stem


# ------------------------------------------------------------------ ingestion

BODY = """\
> **NON-AUTHORITATIVE.** This is a convenience copy for machine reading. The official text is
> published by {issuing_body} at the source URL above. Verify at source before relying on it.

# {title} ({citation})

## At a glance

{glance}

## Full text

{text}
"""


def frontmatter_for(*, jurisdiction, sid, title, doc_type, citation, authority_level,
                    issuing_body, url, fmt, retrieved, sha, tags) -> dict:
    """The document's frontmatter. Order, defaults and validation are the toolkit's
    (`write_document`); what is here is what this corpus asserts."""
    return {
        "schema_version": 1, "corpus": "oregon-counties", "jurisdiction": jurisdiction,
        "id": sid, "title": title, "doc_type": doc_type, "citation": citation,
        "authority_level": authority_level, "issuing_body": issuing_body,
        "source_url": url, "source_format": fmt, "retrieved": retrieved,
        "source_sha256": sha, "snapshot_policy": "hash-only",
        "effective_date": None, "source_version": None, "status": "current",
        "content_mode": "verbatim", "last_verified": "", "verified_by": "",
        "maintainer": "OregonAI",
        "relationships": {"implements": [], "implemented_by": [], "references_external": [],
                          "related": [], "supersedes": []},
        "tags": list(tags),
    }


def ingest_county(slug: str, config, refetch: bool = False, limit: int | None = None,
                  profile: dict | None = None) -> int:
    group_path = SOURCES / f"{slug}.yml"
    if not group_path.is_file():
        print(f"no manifest for {slug}; run --discover first", file=sys.stderr)
        return 1
    group = yaml.safe_load(group_path.read_text(encoding="utf-8"))
    decision = group["crawl"]["decision"]
    if decision in ("excluded", "unavailable"):
        # Both mean "no documents", and they mean opposite things about WHY. `excluded` is a
        # choice we made; `unavailable` is a refusal we were handed. Reported distinctly so
        # a reader of the log — and of STATUS.md — is never left to infer that a county
        # publishes nothing when in fact we could not reach what it publishes.
        why = ("deliberately not ingested" if decision == "excluded"
               else "the host refused an honestly-identified agent")
        print(f"{slug}: crawl decision is '{decision}' — {why}. Nothing ingested, and this "
              f"is a fact about our access, not about the county.")
        return 0

    registry = {c["slug"]: c for c in
                yaml.safe_load((ROOT / "_meta" / "counties.yml").read_text())["counties"]}
    county = registry[f"{slug}-county"]
    body_name = ("County Court" if county["governing_body"] == "county-court"
                 else "Board of Commissioners")
    issuing = f"{county['name']} {body_name}"

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for i, src in enumerate(group["sources"][:limit], 1):
        sid, family = src["id"], src["family"]
        try:
            snap = SNAPSHOTS / f"{sid}.{src['format']}"
            raw, fresh = fetch.snapshot(src["url"], snap, refetch)
            fmt = fetch.sniff(raw, src["format"])
            if fmt in fetch.UNSUPPORTED:
                raise ValueError(f"{fmt.upper()} file, not a document this corpus can read "
                                 f"(usually an application form rather than law)")
            if fmt != src["format"]:
                # Sniffed format wins and the manifest is corrected. A PDF served from an
                # extensionless URL and recorded as html makes corpus-detect-changes convert
                # HTML-to-text over PDF bytes and report CHANGED on every run, forever.
                print(f"  [{i}] {sid}: manifest says {src['format']}, bytes say {fmt}")
                src["format"] = fmt
                snap = snap.with_suffix(f".{fmt}")
                snap.write_bytes(raw)

            # A profile may supply its own extractor. Needed wherever a county's documents
            # are not files but API responses: Washington's code arrives as Municode JSON,
            # which extract_html would happily turn into a page of punctuation.
            custom = getattr((profile or {}).get("_module"), "extract", None)
            if custom is not None:
                text, stats = custom(raw, fmt, src)
            elif fmt == "pdf":
                text, stats = extract.extract_pdf(raw)
            else:
                text, stats = extract.extract_html(raw)
            extract.assert_extracted(text, sid)
            # The toolkit writes <sid>.txt, hashes both ways and moves this source's drift
            # baseline in the group file (ADR-0016). The in-memory record follows so the
            # whole-file rewrite below carries the same value.
            recorded = record_snapshot(config, sid, raw, fmt, text)
            src["sha256"] = recorded.content_hash

            doc_dir = COUNTIES / f"{slug}-county" / family
            doc_path = doc_dir / f"{sid}.md"
            _, retrieved = fetch.source_dates(snap, fresh, doc_path)

            title, citation = src["title"], src.get("citation") or src["title"]
            write_document(config, doc_path, frontmatter_for(
                jurisdiction=f"oregon/{slug}-county", sid=sid, title=title,
                doc_type=FAMILY_DOCTYPE[family], citation=citation,
                authority_level=FAMILY_AUTHORITY[family], issuing_body=issuing,
                url=src["url"], fmt=fmt, retrieved=retrieved, sha=recorded.sha256,
                tags=[f"{slug}-county", family]),
                BODY.format(issuing_body=issuing, title=title, citation=citation,
                            glance=f"{_titleize(src['title'])} — {family.replace('-', ' ')} of "
                                   f"{county['name']}. "
                                   f"{', '.join(f'{v} {k}' for k, v in stats.items())}.",
                            text=text))
            ok += 1
        except Exception as e:                    # noqa: BLE001 — reported, not hidden
            failed += 1
            print(f"  [{i}] {sid}  FAILED: {type(e).__name__}: {e}", file=sys.stderr)

    group_path.write_text(yaml.safe_dump(group, sort_keys=False, allow_unicode=True,
                                         width=100), encoding="utf-8")
    print(f"{slug}: {ok} ingested, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", metavar="COUNTY")
    ap.add_argument("--only", metavar="COUNTY")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    profiles = load_profiles()
    if args.list:
        for slug, p in sorted(profiles.items()):
            fams = ", ".join(p["families"])
            print(f"{slug:<12} {p['discovery']:<14} {p['crawl']['decision']:<12} {fams}")
        return 0
    if args.discover:
        return run_discovery(args.discover, profiles)

    config = config_mod.load(ROOT / "_meta" / "corpus.yml")
    targets = sorted(profiles) if args.all else [args.only] if args.only else []
    if not targets:
        ap.error("one of --discover, --only, --all, --list")
    return max(ingest_county(t, config, args.refetch, args.limit, profiles.get(t))
               for t in targets)


if __name__ == "__main__":
    sys.exit(main())
