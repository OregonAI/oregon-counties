"""Text extraction shared by every county profile.

PORTED, NOT REIMPLEMENTED. `guard_headings`, `page_furniture` and the FURNITURE_BAND
discipline come from federal-reference/src/ingest_instruments.py, which got them from
oregon-audits, which got them from oregon-records-retention. Each carries a bug that was
paid for once already, and county PDFs will hit both harder than any corpus so far: 36
counties of code chapters, board orders and comprehensive plans are dense with numbered
headings and heavy page furniture.
"""
from __future__ import annotations

import io
import pathlib
import re

from pypdf import PdfReader

# Learn and remove running headers/footers ONLY in the first and last three non-blank lines
# of a page. See strip_furniture() for why the band is not optional.
FURNITURE_BAND = 3

# Below this, an extraction is a scanned image or a broken download, not a short document.
MIN_CHARS = 500


def guard_headings(text: str) -> str:
    r"""Never let SOURCE text start a line with `## `.

    corpus_toolkit.repo.FULLTEXT_RE is `^## Full text\s*$(.*?)(?=^## |\Z)`, so the FIRST line
    beginning `## ` at column zero ends the document there. A leading space stops the match,
    and normalize_ws() erases it before any comparison, so source_sha256 and the in-order
    line check are unaffected.

    THE FAILURE IS SILENT AND SURVIVES CI. Coverage thresholds are fail 0.70 / warn 0.90, so
    a stray `## ` in the last tenth of a long document truncates the tail and still scores
    above 90%, and the in-order check passes because a truncated document's lines are all
    still present and still in order. Measured: federal-reference shipped 1 character of
    632,927; oregon-audits report 2021-36 shipped 58,359 of 111,606.

    Apply this to EVERY extracted text, from every source format, without exception. Headings
    this corpus emits itself use `###`, which does not match the lookahead.
    """
    return re.sub(r"^(#{1,6}\s)", r" \1", text, flags=re.M)


def page_furniture(pages: list[list[str]]) -> tuple[set[str], set[str]]:
    """Lines repeated at the top/bottom of most pages: letterhead, banners, footers."""
    if len(pages) < 4:
        return set(), set()
    top: dict[str, int] = {}
    bot: dict[str, int] = {}
    for p in pages:
        for line in [x.strip() for x in p[:FURNITURE_BAND] if x.strip()]:
            top[line] = top.get(line, 0) + 1
        for line in [x.strip() for x in p[-FURNITURE_BAND:] if x.strip()]:
            bot[line] = bot.get(line, 0) + 1
    half = len(pages) / 2
    return ({l for l, n in top.items() if n > half},
            {l for l, n in bot.items() if n > half})


def is_page_number(line: str, npages: int) -> bool:
    s = line.strip()
    return bool(re.fullmatch(r"(page\s+)?\d{1,4}(\s*(of|/)\s*\d{1,4})?", s, re.I)) \
        and len(s) <= 18 and npages > 1


def extract_pdf(data: bytes | pathlib.Path) -> tuple[str, dict]:
    """PDF -> text, stripping page furniture ONLY where page furniture can occur.

    THE BAND IS THE WHOLE POINT. Running both filters against every line on every page
    deletes real body text: a wrapped citation whose number lands on its own line reads as a
    page number and disappears. That is not hypothetical — CJIS SP 6.1 shipped with the year
    "2006" and the standard number "124" removed from body prose, both from an
    incorporated-by-reference appendix. Silently truncating the identifier of an incorporated
    standard is exactly the wrong-document failure a law corpus cannot afford, and provenance
    could not catch it: the committed text and the snapshot agreed, because both came from
    the same broken extractor.

    page_furniture() only ever LEARNS from the band, so applying what it learned outside the
    band was never justified.
    """
    raw = data if isinstance(data, bytes) else pathlib.Path(data).read_bytes()
    reader = PdfReader(io.BytesIO(raw))
    pages = [(p.extract_text() or "").splitlines() for p in reader.pages]
    top, bot = page_furniture(pages)
    npages = len(pages)

    out: list[str] = []
    for lines in pages:
        stripped = [x.strip() for x in lines]
        filled = [i for i, s in enumerate(stripped) if s]
        if not filled:
            continue
        band = set(filled[:FURNITURE_BAND]) | set(filled[-FURNITURE_BAND:])
        for i, s in enumerate(stripped):
            if i in band and (s in top or s in bot or is_page_number(s, npages)):
                continue
            out.append(lines[i].rstrip())
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return guard_headings(text), {"pages": npages}


def extract_html(raw: bytes) -> tuple[str, dict]:
    """HTML -> text via the toolkit's converter, so drift detection and ingestion agree.

    corpus-detect-changes hashes `content_hash(fetch(url), 'html')`, which calls the same
    html_to_text. Using a different converter here would make every source read as CHANGED
    forever while looking correct — the manifest hash and the document hash are different
    quantities and only stay comparable if the same converter produced both.
    """
    from corpus_toolkit.html_to_text import html_to_text
    text = html_to_text(raw)              # takes bytes, not str
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return guard_headings(text), {"characters": len(text)}


def assert_extracted(text: str, what: str, minimum: int = MIN_CHARS) -> None:
    """Raise unless the extraction produced a plausible document.

    Checked EXPLICITLY rather than left to provenance coverage, because coverage compares
    the committed text against the snapshot — and a scanned PDF that yields 40 characters
    matches its own snapshot perfectly. The floor is what distinguishes 'this document is
    short' from 'this PDF is an image and we extracted nothing'.
    """
    if len(text) < minimum:
        raise ValueError(f"{what}: only {len(text)} chars extracted "
                         f"(<{minimum}) — scanned image or broken download")
