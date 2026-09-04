#!/usr/bin/env python3
"""Recover image-only scans into `## Full text` under the two-engine rule.

    python3 src/ocr_recover.py --county wasco --limit 10
    python3 src/ocr_recover.py --county wasco --dry-run     # score only, write nothing
    python3 src/ocr_recover.py --all

IMPLEMENTS AGENTS.md's OCR section and the two-engine rule it inherits from
`oregon-policy-repo/AGENTS.md`. A single engine's output is never promotable. Two engines
that share no model weights are vanishingly unlikely to invent the SAME words, so high
agreement is positive evidence the words are physically on the page. That evidence — not a
better engine — is what makes promotion defensible.

    engine 1   ocrmypdf (tesseract), writing a text layer into a COPY
    engine 2   PaddleOCR (PP-OCRv6), reading the ORIGINAL scan

Engine 2 must read the original, not engine 1's output: corroborating against the other
engine's own text is an echo, not evidence.

GATES, all of which must pass:
    >= 100 words                       a scrap of letterhead is not a document
    word agreement >= 0.80             difflib over [a-z]{2,} tokens, lowercased
    dictionary ratio >= 0.80           on engine 1's output

FIGURES ARE SCORED SEPARATELY AND ARE NOT A GATE. AGENTS.md records word agreement running
88-98% while agreement on FIGURES ran 69-85% on the same documents — digits are exactly where
two engines diverge, and a single headline number hides it. Recorded in conversion_notes so a
reader knows how much to trust a number in the text; a low figure score means human review,
not rejection.

THE DICTIONARY IS NEVER BUILT FROM THIS CORPUS. AGENTS.md's first trap: OCR errors entering
the vocabulary that judges them makes every OCR'd document score 100% however badly it was
read — a gate that cannot fail is worse than none, because it looks like evidence. This uses
`english_words` (web2, 234,450 entries) plus plain suffix stripping, which is morphology and
not corpus contamination.

CALIBRATED BEFORE USE, on 12 known-good text-layer documents from this corpus: they score
0.897-0.993, mean 0.946. So the 0.80 bar has real headroom and a document failing it is
genuinely degraded rather than merely legal-sounding.

WHAT THIS NEVER DOES: replace or "improve" text that already exists (OCR may only ADD text
where a document has none); repair artefacts such as lost word spacing (re-inserting word
boundaries means writing text the OCR did not resolve); or use a generative/VLM model for
transcription. A generative model asked to read a blurry legal scan emits fluent, plausible,
WRONG statutory language. A purpose-built engine garbles visibly instead, and visible garbage
is a safety property — it fails the gate rather than passing as text.
"""
from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import subprocess
import sys
import tempfile
import time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from corpus_toolkit import config as config_mod        # noqa: E402
from corpus_toolkit.documents import write_document    # noqa: E402
from corpus_toolkit.sources.snapshots import record_snapshot  # noqa: E402
from src import extract, fetch                         # noqa: E402
from src.ingest_counties import (BODY, FAMILY_AUTHORITY,  # noqa: E402
                                 FAMILY_DOCTYPE, _titleize, frontmatter_for)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_meta" / "sources"
SNAPSHOTS = ROOT / "_meta" / "snapshots"
CONFIG = config_mod.load(ROOT / "_meta" / "corpus.yml")
COUNTIES = ROOT / "counties"

MIN_WORDS = 100
MIN_AGREEMENT = 0.80
MIN_DICT = 0.80
# Above this the PDF already has a usable text layer and OCR must not touch it.
HAS_TEXT_CHARS = 500

_WORDS = re.compile(r"[a-z]{2,}")
_FIGURES = re.compile(r"\d+")


# ----------------------------------------------------------------- dictionary

def _vocab():
    from english_words import get_english_words_set
    return get_english_words_set(["web2"], lower=True)


_BASE = None
_SUFFIXES = (("s", ""), ("es", ""), ("ed", ""), ("ing", ""), ("ies", "y"),
             ("d", ""), ("ly", ""), ("er", ""), ("est", ""))


def _known(word: str) -> bool:
    """In the wordlist, or a plain suffixed form of something in it.

    web2 has `ordinance` and `zoning` but not `commissioners`, and a legal corpus is full of
    plurals. Stripping suffixes is morphology; it does not let OCR errors in, which is the
    property that matters — `pernitted` and `conmissioner` still fail.
    """
    if word in _BASE:
        return True
    return any(word.endswith(s) and (word[:-len(s)] + r) in _BASE for s, r in _SUFFIXES)


def dictionary_ratio(text: str) -> tuple[float, int]:
    words = _WORDS.findall(text.lower())
    if not words:
        return 0.0, 0
    return sum(1 for w in words if _known(w)) / len(words), len(words)


def agreement(a: str, b: str) -> tuple[float, float | None]:
    """(word agreement, figure agreement) between two engines' output."""
    wa, wb = _WORDS.findall(a.lower()), _WORDS.findall(b.lower())
    fa, fb = _FIGURES.findall(a), _FIGURES.findall(b)
    w = difflib.SequenceMatcher(None, wa, wb).ratio() if (wa and wb) else 0.0
    f = difflib.SequenceMatcher(None, fa, fb).ratio() if (fa and fb) else None
    return w, f


# ----------------------------------------------------------------- engines

def engine_tesseract(pdf: pathlib.Path, work: pathlib.Path) -> str:
    """ocrmypdf writes a text layer into a COPY — never over the original.

    The original stays the exact bytes upstream served, so `source_sha256` continues to hash
    what the county published. OCR is a local text-recovery step, not a source refresh.

    `--rotate-pages` is not decoration: AGENTS.md records tesseract leaving a page upside
    down at default OSD confidence and emitting `:Peusiiqnd` for `Published:` — thousands of
    characters of confident garbage that passes every length check.
    """
    out = work / "ocr.pdf"
    subprocess.run(["ocrmypdf", "-l", "eng", "--optimize", "0", "--output-type", "pdf",
                    "--rotate-pages", "--deskew", "--force-ocr", "--quiet",
                    str(pdf), str(out)], check=True, capture_output=True, timeout=900)
    txt = work / "t1.txt"
    subprocess.run(["pdftotext", "-layout", str(out), str(txt)],
                   check=True, capture_output=True, timeout=300)
    return txt.read_text(encoding="utf-8", errors="replace")


_PADDLE = None


def engine_paddle(pdf: pathlib.Path) -> str:
    """PaddleOCR on the ORIGINAL scan, with orientation classification ON.

    Not optional: AGENTS.md records the same rotated page scoring 0.050 against tesseract
    with `use_doc_orientation_classify=False` and 0.929 with it on. Same page, same engines.
    Without it the corroboration check quietly becomes an orientation check.
    """
    global _PADDLE
    if _PADDLE is None:
        import warnings
        warnings.filterwarnings("ignore")
        from paddleocr import PaddleOCR
        _PADDLE = PaddleOCR(use_doc_orientation_classify=True, use_doc_unwarping=False,
                            use_textline_orientation=True, lang="en")
    lines: list[str] = []
    for page in _PADDLE.predict(str(pdf)):
        lines += page.get("rec_texts", [])
    return "\n".join(lines)


# ----------------------------------------------------------------- driver

BANNER = (
    "> **NON-AUTHORITATIVE — OCR-DERIVED TEXT, NOT HUMAN-VERIFIED.** The county publishes\n"
    "> this document as an image-only scan with no text layer. The text below was read by\n"
    "> two independent OCR engines that agreed at {agree:.0%}; it is a machine reading of a\n"
    "> picture, not the county's own text. Verify at the source URL before relying on it.\n")

CURATOR = """
## Curator notes

This document had no text layer. The text above was recovered by OCR under the two-engine
rule in `AGENTS.md`: `{e1}` and `{e2}` read it independently and agreed on {agree:.1%} of
the word sequence{figs}. Dictionary-recognizable words: {dratio:.1%}.

**Agreement is evidence the words are on the page. It is not evidence they were read
correctly** — two engines can misread the same smudged character identically. Signature
blocks, proper names, dates and dollar figures are the least reliable parts of an OCR'd
scan, and figures diverge between engines more than words do.

Nothing has been repaired. Where the engines lost word spacing or garbled a character, that
is left visible rather than corrected, because re-inserting what OCR did not resolve means
writing text no one read.
"""


def candidates(slug: str) -> list[dict]:
    path = SOURCES / f"{slug}.yml"
    group = yaml.safe_load(path.read_text(encoding="utf-8"))
    out = []
    for s in group.get("sources") or []:
        doc = COUNTIES / f"{slug}-county" / s["family"] / f"{s['id']}.md"
        if not doc.is_file() and s.get("format") == "pdf":
            out.append(s)
    return out


def recover(slug: str, src: dict, registry: dict, dry: bool) -> str:
    sid = src["id"]
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td)
        pdf = work / "in.pdf"
        # ONE BAD URL MUST NOT END THE BATCH. Columbia links a 404 in its ordinance index,
        # and an unguarded fetch took the whole 19-county run down with it. Per-source
        # failures are reported and stepped over, exactly like extraction failures.
        try:
            raw, _ = fetch.snapshot(src["url"], pdf, refetch=True)
        except Exception as e:                        # noqa: BLE001 — reported, not hidden
            return f"fail: fetch {type(e).__name__}: {str(e)[:44]}"

        if not raw.startswith(b"%PDF"):
            return "skip: not a PDF"
        try:
            existing, _ = extract.extract_pdf(raw)
        except Exception:
            existing = ""
        if len(existing) >= HAS_TEXT_CHARS:
            # OCR may only ADD text where there is none. Never replace or "improve".
            return f"skip: already has {len(existing)} chars of text layer"

        try:
            t1 = engine_tesseract(pdf, work)
        except subprocess.CalledProcessError as e:
            return f"fail: tesseract {e.returncode}"
        except subprocess.TimeoutExpired:
            return "fail: tesseract timeout"
        try:
            t2 = engine_paddle(pdf)
        except Exception as e:                        # noqa: BLE001 — reported, not hidden
            return f"fail: paddle {type(e).__name__}"

        wr, fr = agreement(t1, t2)
        dr, nwords = dictionary_ratio(t1)
        figs = "" if fr is None else f", and on {fr:.1%} of the figures"
        score = (f"words={nwords} agree={wr:.3f} "
                 f"fig={'n/a' if fr is None else f'{fr:.3f}'} dict={dr:.3f}")

        if nwords < MIN_WORDS:
            return f"reject: {score} (<{MIN_WORDS} words)"
        if wr < MIN_AGREEMENT:
            return f"reject: {score} (agreement <{MIN_AGREEMENT})"
        if dr < MIN_DICT:
            return f"reject: {score} (dictionary <{MIN_DICT})"
        if dry:
            return f"PASS (dry-run): {score}"

        text = extract.guard_headings(re.sub(r"\n{3,}", "\n\n", t1).strip())
        # The toolkit writes <sid>.txt and <sid>.pdf (the latter gitignored), hashes both
        # ways and moves the drift baseline (ADR-0016).
        recorded = record_snapshot(CONFIG, sid, raw, "pdf", text)

        county = registry[f"{slug}-county"]
        body_name = ("County Court" if county["governing_body"] == "county-court"
                     else "Board of Commissioners")
        doc_dir = COUNTIES / f"{slug}-county" / src["family"]
        title = src.get("title") or _titleize(sid)
        citation = src.get("citation") or src.get("title") or sid
        issuing = f"{county['name']} {body_name}"
        fm = frontmatter_for(
            jurisdiction=f"oregon/{slug}-county", sid=sid, title=title,
            doc_type=FAMILY_DOCTYPE[src["family"]], citation=citation,
            authority_level=FAMILY_AUTHORITY[src["family"]], issuing_body=issuing,
            url=src["url"], fmt="pdf", retrieved=time.strftime("%Y-%m-%d"),
            sha=recorded.sha256, tags=[f"{slug}-county", src["family"], "ocr-derived"])
        # Disclose provenance in frontmatter: OCR-derived, two engines, agreement figures.
        fm["text_source"] = "ocr"
        fm["conversion_notes"] = (
            f"OCR-derived. Engines: ocrmypdf/tesseract 5.3.4 and PaddleOCR PP-OCRv6, run "
            f"independently on the same scan. Word agreement {wr:.3f}; figure agreement "
            f"{'n/a' if fr is None else f'{fr:.3f}'}; dictionary ratio {dr:.3f}. Artifacts "
            f"disclosed, not repaired. NOT human-verified.")
        body = BODY.format(issuing_body=issuing, title=title, citation=citation,
                           glance=f"OCR-derived text of {title}. Not human-verified.", text=text)
        # Swap the generic banner for the OCR one.
        body = re.sub(r"> \*\*NON-AUTHORITATIVE\.\*\*.*?\n\n", BANNER.format(agree=wr) + "\n",
                      body, count=1, flags=re.S)
        body = body.rstrip() + "\n" + CURATOR.format(
            e1="ocrmypdf/tesseract", e2="PaddleOCR PP-OCRv6",
            agree=wr, figs=figs, dratio=dr)
        write_document(CONFIG, doc_dir / f"{sid}.md", fm, body)
        return f"PROMOTED: {score}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--county")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    global _BASE
    _BASE = _vocab()

    registry = {c["slug"]: c for c in
                yaml.safe_load((ROOT / "_meta" / "counties.yml").read_text())["counties"]}
    slugs = ([p.stem for p in sorted(SOURCES.glob("*.yml"))] if args.all
             else [args.county] if args.county else [])
    if not slugs:
        ap.error("--county or --all")

    tally: dict[str, int] = {}
    for slug in slugs:
        cands = candidates(slug)[:args.limit]
        if not cands:
            continue
        print(f"\n=== {slug}: {len(cands)} candidate(s)")
        for i, s in enumerate(cands, 1):
            r = recover(slug, s, registry, args.dry_run)
            kind = r.split(":")[0].split(" ")[0]
            tally[kind] = tally.get(kind, 0) + 1
            print(f"  [{i}/{len(cands)}] {s['id'][:56]:<58} {r}")

    print("\n" + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
