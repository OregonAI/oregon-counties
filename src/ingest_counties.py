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
from corpus_toolkit.repo import hash_snapshot            # noqa: E402
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
    body, _ = fetch.get(cfg["listing_url"])
    html = body.decode("utf-8", "replace")
    base = cfg.get("base_url") or cfg["listing_url"]
    m = re.search(r'<base[^>]+href\s*=\s*["\']([^"\']+)', html, re.I)
    if m:
        base = urllib.parse.urljoin(cfg["listing_url"], m.group(1))

    link_re = re.compile(cfg["link_re"], re.I)
    seen, out = set(), []
    for match in link_re.finditer(html):
        href = match.group(1).strip()
        url = urllib.parse.urljoin(base, href)
        if url in seen:
            continue
        seen.add(url)
        name = urllib.parse.unquote(url.rsplit("/", 1)[-1])
        if fetch.looks_like_draft(name) or fetch.looks_like_draft(href):
            continue
        if cfg.get("exclude_re") and re.search(cfg["exclude_re"], url, re.I):
            continue
        out.append({"url": url, "name": name})
    return out


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


def discover_municode(profile: dict, family: str, cfg: dict) -> list[dict]:
    """Municode — the JSON API, which is open while the HTML library index 403s.

    `ClientContent/<id>` is the staleness test, not `Jobs/latest/<id>`, which returns 204 for
    every Oregon client and so tests nothing. A client record can exist with
    `latestUpdatedDate: null` and no content at all — Lincoln County has exactly that, and
    recording it as a source would have been a fabricated one.
    """
    body, _ = fetch.get(f"https://api.municode.com/ClientContent/{cfg['client_id']}")
    payload = json.loads(body)
    out = []
    for code in payload.get("codes", []):
        if cfg.get("product_id") and code.get("productId") != cfg["product_id"]:
            continue
        if not code.get("latestUpdatedDate"):
            continue                       # an empty shell, not a code
        out.append({
            "url": f"https://api.municode.com/codesToc?jobId=&productId={code['productId']}",
            "name": code["productName"],
            "product_id": code["productId"],
            "updated": code["latestUpdatedDate"],
        })
    return out


DISCOVERY = {
    "link-list": discover_link_list,
    "mco-s3": discover_mco_s3,
    "municode-api": discover_municode,
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
                "id": cfg["id_fn"](item) if callable(cfg.get("id_fn"))
                      else f"{slug}-{family}-{_slugify(item['name'])}",
                "url": item["url"],
                "family": family,
                "format": cfg.get("format", "pdf"),
                "sha256": "",
                "title": item.get("title") or _titleize(item["name"]),
                "last_checked": time.strftime("%Y-%m-%d"),
            })
        print(f"  {family:<10} {len(found)} source(s)")

    SOURCES.mkdir(parents=True, exist_ok=True)
    out = SOURCES / f"{slug}.yml"
    out.write_text(yaml.safe_dump(group, sort_keys=False, allow_unicode=True, width=100),
                   encoding="utf-8")
    print(f"wrote {out}  ({len(group['sources'])} sources) — REVIEW BEFORE INGESTING")
    return 0


def _slugify(name: str) -> str:
    stem = re.sub(r"\.[a-z0-9]{2,4}$", "", name, flags=re.I)
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")[:60]


def _titleize(name: str) -> str:
    return re.sub(r"\.[a-z0-9]{2,4}$", "", name, flags=re.I).replace("_", " ").strip()


# ------------------------------------------------------------------ ingestion

DOC = """\
---
schema_version: 1
corpus: oregon-counties
jurisdiction: {jurisdiction}
id: {id}
title: {title!r}
doc_type: {doc_type}
citation: {citation!r}
authority_level: {authority_level}
issuing_body: {issuing_body!r}
source_url: {url}
source_format: {fmt}
retrieved: '{retrieved}'
source_sha256: {sha}
snapshot_policy: hash-only
effective_date: null
source_version: null
status: current
content_mode: verbatim
last_verified: ''
verified_by: ''
maintainer: 'OregonAI'
relationships:
  implements: []
  implemented_by: []
  references_external: []
  related: []
  supersedes: []
tags: [{tags}]
---

> **NON-AUTHORITATIVE.** This is a convenience copy for machine reading. The official text is
> published by {issuing_body} at the source URL above. Verify at source before relying on it.

# {title} ({citation})

## At a glance

{glance}

## Full text

{text}
"""


def ingest_county(slug: str, config, refetch: bool = False, limit: int | None = None) -> int:
    group_path = SOURCES / f"{slug}.yml"
    if not group_path.is_file():
        print(f"no manifest for {slug}; run --discover first", file=sys.stderr)
        return 1
    group = yaml.safe_load(group_path.read_text(encoding="utf-8"))
    if group["crawl"]["decision"] == "excluded":
        print(f"{slug}: crawl decision is 'excluded' — nothing ingested by design")
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
            if fmt != src["format"]:
                # Sniffed format wins and the manifest is corrected. A PDF served from an
                # extensionless URL and recorded as html makes corpus-detect-changes convert
                # HTML-to-text over PDF bytes and report CHANGED on every run, forever.
                print(f"  [{i}] {sid}: manifest says {src['format']}, bytes say {fmt}")
                src["format"] = fmt
                snap = snap.with_suffix(f".{fmt}")
                snap.write_bytes(raw)

            text, stats = (extract.extract_pdf(raw) if fmt == "pdf"
                           else extract.extract_html(raw))
            extract.assert_extracted(text, sid)
            (SNAPSHOTS / f"{sid}.txt").write_text(text, encoding="utf-8")

            doc_dir = COUNTIES / f"{slug}-county" / family
            doc_dir.mkdir(parents=True, exist_ok=True)
            doc_path = doc_dir / f"{sid}.md"
            _, retrieved = fetch.source_dates(snap, fresh, doc_path)

            doc_path.write_text(DOC.format(
                jurisdiction=f"oregon/{slug}-county", id=sid, title=src["title"],
                doc_type=FAMILY_DOCTYPE[family],
                citation=src.get("citation") or src["title"],
                authority_level=FAMILY_AUTHORITY[family], issuing_body=issuing,
                url=src["url"], fmt=fmt, retrieved=retrieved,
                sha=hash_snapshot(sid, fmt, SNAPSHOTS),
                tags=", ".join([f"{slug}-county", family]),
                glance=f"{_titleize(src['title'])} — {family.replace('-', ' ')} of "
                       f"{county['name']}. "
                       f"{', '.join(f'{v} {k}' for k, v in stats.items())}.",
                text=text), encoding="utf-8")
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
    return max(ingest_county(t, config, args.refetch, args.limit) for t in targets)


if __name__ == "__main__":
    sys.exit(main())
