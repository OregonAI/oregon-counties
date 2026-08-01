#!/usr/bin/env python3
"""Recover citations that a defective PDF text layer renders as impossible ORS chapters.

    python3 src/relayer_citations.py --dry-run     # score and report, write nothing
    python3 src/relayer_citations.py               # write the recovered edges

THE PROBLEM (issue #10). Twelve Deschutes documents and one Curry document cite chapters
that cannot exist:

    our full text     ORS 46813.095      the printed page     ORS 468B.095
                      ORS 27913.050                           ORS 279B.050
                      ORS 2798.085                            ORS 279B.085

The PDF's embedded text layer decodes the `B` of a lettered chapter as `13` or `8`. Our
extraction is FAITHFUL — `pdftotext` on the source file reproduces it exactly — so this is
not an extraction bug on our side. It is the source file's own font encoding, and it is
confined to citation runs: in the same document `B` decodes correctly 56 times, `Board`
included.

WHY THIS SCRIPT AND NOT `ocr_recover.py`. That tool's rule is "OCR may only ADD text where a
document has none; never replace or improve" (it returns `skip: already has N chars of text
layer` at 500 chars). The rule is right and this script does not weaken it:

  * `## Full text` IS NEVER TOUCHED. It mirrors the source file, and the source file really
    does say `46813.095`. Rewriting it would make the corpus assert that the county published
    something it did not, and would break provenance, which re-derives every line from the
    committed snapshot.
  * Only `relationships.references_external` — a DERIVED field, our own reading of what the
    document points at — is corrected, and only with recorded evidence.

THE CORRECTION IS DATA, NOT AN EDIT. This writes `_meta/citation-corrections.yml` and
`link_citations.py` consults it; nothing here rewrites a document. Editing the documents
directly would not survive: `link_citations.py --check` is a CI gate that recomputes
references_external from the verbatim text, so a hand-applied correction is reported as drift
on the next run and reverted by the next real one — the fix would undo itself and CI would
call the undoing correct. As a file, the correction is also reviewable in one place, with its
evidence beside it, instead of scattered across thirteen frontmatter blocks.

A reader still sees the malformed citation in the verbatim text; `conversion_notes` tells them
why it is malformed and what the page actually prints.

THE TWO-ENGINE RULE STILL APPLIES, because this is still a machine reading a picture. Both
engines read the ORIGINAL rendered page independently; neither sees the other's output, and
neither sees the broken text layer.

ACCEPTANCE — all four, per citation. Anything less is left alone and reported:

  1. STRUCTURALLY IMPOSSIBLE TRIGGER. Only citations whose chapter has 4+ digits are
     candidates. Real ORS chapters are at most three digits plus an optional letter, so
     `27913` is not a chapter that might exist and that we lack — it is not a chapter. This
     keeps the script off anything that is merely unresolved.
  2. SAME SECTION NUMBER. The recovered citation's section must equal the broken one's
     exactly (`.095` -> `.095`). Without this the script could pick up any nearby citation
     and call it the answer.
  3. NUMERIC PREFIX. The recovered chapter's digits must be a prefix of the broken chapter's
     digits (`468` of `46813`, `279` of `2798`). This is what ties the reading to THIS
     citation rather than to a plausible neighbour, and it is why a wholesale "find the
     nearest ORS number" approach was not used.
  4. BOTH ENGINES AGREE on the result.

WHAT IS DELIBERATELY NOT DONE: no find-and-replace of `13`->`B` anywhere. That transformation
is the hypothesis, not the evidence, and applying it directly would manufacture citations that
look verified. Every recovered citation here was read off the rendered page twice.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

# Both roots: `src/` so sibling modules import, and the repo root because fetch.py imports
# `src.patterns` by package path.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import extract                                        # noqa: E402
import fetch                                          # noqa: E402
from corpus_toolkit.repo import hash_snapshot         # noqa: E402
from ocr_recover import engine_paddle                 # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
COUNTIES = ROOT / "counties"

# A chapter of 4+ digits cannot exist. This is the whole trigger — see acceptance rule 1.
IMPOSSIBLE = re.compile(r"\bORS\s+(?P<chap>\d{4,})\.(?P<sec>\d{3,})\b")
# A structurally legal ORS citation, for reading candidates out of OCR output.
LEGAL = re.compile(r"\bORS\s+(?P<chap>\d{1,3}[A-Z]?)\.(?P<sec>\d{3,})\b")

RENDER_DPI = 300


def page_of(pdf: pathlib.Path, chap: str, sec: str) -> list[int]:
    """1-based pages whose extracted text carries this citation.

    Uses the BROKEN layer on purpose: it is the only thing that knows where the citation
    sits. It is trusted for location only, never for content.

    WHITESPACE-TOLERANT, and that is not cosmetic. Raw `pdftotext` on these files emits
    `27913. 050` — a space after the period — where the ingest's own extractor produced
    `27913.050`. An exact-token search found nothing and the citation was reported as "not
    locatable", which reads as an OCR failure when it was a whitespace difference between
    two extractors of the same page.
    """
    out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, timeout=300)
    text = out.stdout.decode("utf-8", "replace")
    pat = re.compile(rf"{re.escape(chap)}\s*\.\s*{re.escape(sec)}")
    return [i for i, p in enumerate(text.split("\f"), 1) if pat.search(p)]


def tesseract_page(png: pathlib.Path) -> str:
    r = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                       capture_output=True, timeout=300)
    return r.stdout.decode("utf-8", "replace")


def candidates(text: str, chap: str, sec: str) -> set[str]:
    """Legal citations in `text` that could be THIS citation read correctly.

    Rules 2 and 3 together: same section, and a chapter whose digits open the broken
    chapter's digits. `468B.095` qualifies for `46813.095`; `468.095` also qualifies and is
    kept, because a missing letter is a possible true reading and the engines must still
    agree on which one it is.
    """
    out = set()
    for m in LEGAL.finditer(text):
        if m.group("sec") != sec:
            continue
        digits = re.match(r"\d+", m.group("chap")).group(0)
        if chap.startswith(digits) and len(digits) < len(chap):
            out.add(f"ORS {m.group('chap')}.{m.group('sec')}")
    return out


def recover_doc(path: pathlib.Path) -> tuple[list[str], dict | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    broken = sorted({(m.group("chap"), m.group("sec")) for m in IMPOSSIBLE.finditer(text)})
    if not broken:
        return [], None

    url = re.search(r"^source_url:\s*(\S+)", text, re.M)
    sha = re.search(r"^source_sha256:\s*\"?([0-9a-f]{64})", text, re.M)
    if not url:
        return [f"{path.name}: no source_url — skipped"], None

    log: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td)
        pdf = work / "in.pdf"
        try:
            raw, _ = fetch.snapshot(url.group(1), pdf, refetch=True)
        except Exception as e:                        # noqa: BLE001 — reported, not hidden
            return [f"{path.name}: fetch {type(e).__name__}: {str(e)[:50]}"], None

        # THE SOURCE MUST BE THE ONE WE INGESTED. If the county has replaced the file since,
        # a citation read off today's page is evidence about a different document.
        #
        # `source_sha256` is NOT sha256 of the PDF bytes — `corpus_toolkit.repo.hash_snapshot`
        # hashes the whitespace-normalized EXTRACTED TEXT and only falls back to raw bytes
        # when there is too little of it. Comparing against the raw digest reported all
        # eleven documents as changed, which was this check being wrong rather than the
        # county having replaced every file on the same day. Reproduce it the way the toolkit
        # computes it, using the same extractor that produced the committed snapshot.
        if sha:
            try:
                extracted, _ = extract.extract_pdf(raw)
            except Exception:                         # noqa: BLE001
                extracted = ""
            (work / f"{path.stem}.pdf").write_bytes(raw)
            (work / f"{path.stem}.txt").write_text(extracted, encoding="utf-8")
            if hash_snapshot(path.stem, "pdf", work) != sha.group(1):
                return [f"{path.name}: source_sha256 mismatch — the published file changed "
                        f"since ingestion; skipped rather than mixing two versions"], None

        found: list[dict] = []
        for chap, sec in broken:
            token = f"{chap}.{sec}"
            pages = page_of(pdf, chap, sec)
            if not pages:
                log.append(f"  {token}: not locatable in the text layer — skipped")
                continue
            hits_t: set[str] = set()
            hits_p: set[str] = set()
            for pg in pages:
                subprocess.run(["pdftoppm", "-r", str(RENDER_DPI), "-png", "-f", str(pg),
                                "-l", str(pg), str(pdf), str(work / f"p{pg}")],
                               check=True, capture_output=True, timeout=300)
                png = next(work.glob(f"p{pg}-*.png"), None)
                if png is None:
                    continue
                hits_t |= candidates(tesseract_page(png), chap, sec)
                hits_p |= candidates(engine_paddle(png), chap, sec)

            agreed = hits_t & hits_p                  # acceptance rule 4
            if len(agreed) == 1:
                found.append({"extracted": f"ORS {token}", "printed": agreed.pop(),
                              "page": pages[0]})
            elif not agreed:
                log.append(f"  ORS {token}: engines agreed on nothing "
                           f"(tesseract {sorted(hits_t) or '-'}, paddle {sorted(hits_p) or '-'})")
            else:
                log.append(f"  ORS {token}: engines agreed on MORE THAN ONE "
                           f"({sorted(agreed)}) — ambiguous, left alone")

        if not found:
            return [f"{path.name}: nothing recovered"] + log, None

        log.insert(0, f"{path.name}: recovered {len(found)}")
        for c in found:
            log.append(f"  {c['extracted']}  ->  {c['printed']}   (page {c['page']})")
        row = {"document": path.stem, "source_url": url.group(1),
               "citations": sorted(found, key=lambda c: c["extracted"])}
    return log, row


def write_corrections(rows: list[dict]) -> pathlib.Path:
    """Emit `_meta/citation-corrections.yml` — the whole output of this script.

    Ordered and fully explicit so a reviewer can check any single line against the source PDF
    without re-running anything: which document, what our extraction produced, what the page
    prints, which page it was read from, and which engines agreed.
    """
    out = ROOT / "_meta" / "citation-corrections.yml"
    lines = [
        "# Citations whose chapter letter the source PDF's own text layer decodes as digits.",
        "#",
        "# NOT hand-written and NOT a find-and-replace of 13 -> B. Every `printed` value below",
        "# was read off the page rendered at %ddpi by ocrmypdf/tesseract and PaddleOCR" % RENDER_DPI,
        "# independently, with both engines required to agree, the section number required to",
        "# match exactly, and the recovered chapter's digits required to open the broken",
        "# chapter's digits. Written by src/relayer_citations.py; consumed by",
        "# src/link_citations.py so it survives regeneration. See oregon-counties#10.",
        "#",
        "# The verbatim `## Full text` of these documents is UNCHANGED and still shows the",
        "# malformed citation, because that is what the county's file says.",
        "",
        "documents:",
    ]
    for r in sorted(rows, key=lambda r: r["document"]):
        lines.append(f"  - document: {r['document']}")
        lines.append(f"    source_url: {r['source_url']}")
        lines.append("    citations:")
        for c in r["citations"]:
            lines.append(f"      - extracted: {c['extracted']}")
            lines.append(f"        printed: {c['printed']}")
            lines.append(f"        page: {c['page']}")
            lines.append("        engines: [ocrmypdf/tesseract, PaddleOCR PP-OCRv6]")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    targets = sorted(p for p in COUNTIES.rglob("*.md")
                     if IMPOSSIBLE.search(p.read_text(encoding="utf-8", errors="replace")))
    print(f"{len(targets)} document(s) carry a structurally impossible ORS chapter\n")
    rows, total = [], 0
    for p in targets:
        log, row = recover_doc(p)
        for line in log or [f"{p.name}: no change"]:
            print(line)
        if row:
            rows.append(row)
            total += len(row["citations"])

    verb = "would recover" if a.dry_run else "recovered"
    print(f"\n{verb} {total} citation(s) across {len(rows)} document(s); "
          f"{len(targets) - len(rows)} left alone")
    if rows and not a.dry_run:
        print(f"wrote {write_corrections(rows).relative_to(ROOT)}")
        print("now run: python3 src/link_citations.py && python3 src/build_graph.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
