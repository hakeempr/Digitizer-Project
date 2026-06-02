"""
OCR Engine Service — No external AI API required.

Pipeline:
  1. Pre-process image with OpenCV (deskew, denoise, binarise)
  2. Send to OCR.space with isoverlayrequired=true to get bounding boxes
  3. SmartLayoutAnalyser uses word heights, positions, line density,
     capitalisation, and context to classify each line — no AI API needed.
  4. Falls back to regex patterns if overlay data is unavailable.
"""

import io
import logging
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Image Pre-Processing ─────────────────────────────────────────────────────

def preprocess_image(image_path: str) -> bytes:
    """
    OpenCV pipeline: grayscale → denoise → adaptive threshold → deskew.
    Falls back to raw bytes if OpenCV is not installed.
    """
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")

        gray     = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.medianBlur(gray, 3)
        binary   = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31, C=10,
        )
        binary = _deskew(binary)

        success, buffer = cv2.imencode(".png", binary)
        if not success:
            raise RuntimeError("Failed to encode image.")
        return buffer.tobytes()

    except ImportError:
        logger.warning("OpenCV not installed — skipping pre-processing.")
    except Exception as exc:
        logger.warning("Pre-processing failed: %s — using raw file.", exc)

    with open(image_path, "rb") as f:
        return f.read()


def _deskew(binary_img):
    try:
        import cv2
        import numpy as np

        coords = np.column_stack(np.where(binary_img < 128))
        if len(coords) < 5:
            return binary_img

        angle = cv2.minAreaRect(coords.astype(np.float32))[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:
            return binary_img

        h, w   = binary_img.shape
        center = (w // 2, h // 2)
        M      = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            binary_img, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
    except Exception as exc:
        logger.warning("Deskew failed: %s", exc)
        return binary_img


# ─── OCR.space API Client ─────────────────────────────────────────────────────

class OCRSpaceClient:
    """
    Calls OCR.space with isoverlayrequired=true so we get per-word
    bounding boxes (Left, Top, Width, Height) — essential for smart
    layout analysis without any external AI.
    """

    MAX_RETRIES = 2
    RETRY_DELAY = 3

    def __init__(self):
        self.api_key  = settings.OCR_SPACE_API_KEY
        self.api_url  = settings.OCR_SPACE_API_URL
        self.engine   = settings.OCR_SPACE_ENGINE
        self.language = settings.OCR_SPACE_LANGUAGE

        if not self.api_key:
            raise EnvironmentError(
                "OCR_SPACE_API_KEY is not set in .env. "
                "Get a free key at https://ocr.space/ocrapi/freekey"
            )

    def run_ocr(self, image_path: str) -> dict[str, Any]:
        """
        Returns:
          {
            success   : bool,
            full_text : str,
            lines     : [str, ...],
            pages     : int,
            overlay   : { lines: [...overlay line data...] },
            error     : str | None,
          }
        """
        image_bytes = preprocess_image(image_path)
        filename    = Path(image_path).name
        ext         = Path(image_path).suffix.lower()

        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".gif":  "image/gif",
            ".pdf": "application/pdf",
            ".tif": "image/tiff", ".tiff": "image/tiff",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/png")

        payload = {
            "apikey":               self.api_key,
            "language":             self.language,
            "ocrengine":            self.engine,
            # ← Request bounding box overlay — gives word heights & positions
            "isoverlayrequired":    "true",
            "detectorientation":    "true",
            "scale":                "true",
            "iscreatesearchablepdf":"false",
            "filetype":             ext.lstrip(".").upper() if ext else "PNG",
        }

        last_error = "No attempts made"

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(
                    "OCR attempt %d/%d | file=%s | engine=%d (overlay=true)",
                    attempt, self.MAX_RETRIES, filename, self.engine,
                )

                response = requests.post(
                    self.api_url,
                    data=payload,
                    files={"file": (filename, io.BytesIO(image_bytes), mime_type)},
                    timeout=60,
                )

                logger.info(
                    "OCR.space HTTP %d | %.300s",
                    response.status_code,
                    response.text,
                )

                if response.status_code == 403:
                    return {
                        "success": False, "full_text": "", "lines": [], "pages": 0,
                        "overlay": None,
                        "error": (
                            "OCR.space returned 403 — API key invalid or expired. "
                            "Get a new key at https://ocr.space/ocrapi/freekey"
                        )
                    }

                if response.status_code == 429:
                    return {
                        "success": False, "full_text": "", "lines": [], "pages": 0,
                        "overlay": None,
                        "error": "OCR.space rate limit exceeded. Wait 1 minute."
                    }

                response.raise_for_status()
                return self._parse_response(response.json())

            except requests.exceptions.Timeout:
                last_error = "OCR API timed out after 60s."
                logger.warning("OCR timeout on attempt %d", attempt)
            except requests.exceptions.ConnectionError:
                last_error = "Cannot connect to api.ocr.space."
                logger.warning("OCR connection error on attempt %d", attempt)
            except requests.exceptions.RequestException as exc:
                last_error = f"Request error: {exc}"
                logger.warning("OCR request error attempt %d: %s", attempt, exc)

            if attempt < self.MAX_RETRIES:
                time.sleep(self.RETRY_DELAY)

        return {
            "success": False, "full_text": "", "lines": [], "pages": 0,
            "overlay": None, "error": last_error,
        }

    @staticmethod
    def _parse_response(data: dict) -> dict[str, Any]:
        """Parse OCR.space JSON — extract text AND overlay bounding box data."""

        if data.get("IsErroredOnProcessing"):
            msgs = data.get("ErrorMessage", [])
            error_str = " | ".join(msgs) if isinstance(msgs, list) else str(msgs)
            if not error_str:
                error_str = f"OCR failed (exit code {data.get('OCRExitCode')})"
            return {
                "success": False, "full_text": "", "lines": [], "pages": 0,
                "overlay": None, "error": error_str,
            }

        parsed    = data.get("ParsedResults", [])
        pages     = len(parsed)
        lines     = []
        texts     = []
        all_overlay_lines = []

        for page in parsed:
            page_text = (page.get("ParsedText") or "").strip()
            if page_text:
                texts.append(page_text)
                lines.extend(
                    line.strip()
                    for line in page_text.splitlines()
                    if line.strip()
                )

            # Extract overlay (bounding boxes per line/word)
            overlay = page.get("TextOverlay", {})
            overlay_lines = overlay.get("Lines", [])
            all_overlay_lines.extend(overlay_lines)

        if not texts:
            logger.warning("OCR returned no text.")
            return {
                "success":   True,
                "full_text": "[No text detected in this image]",
                "lines":     ["[No text detected in this image]"],
                "pages":     max(pages, 1),
                "overlay":   {"lines": []},
                "error":     None,
            }

        logger.info(
            "OCR success: %d page(s), %d lines, %d overlay lines",
            pages, len(lines), len(all_overlay_lines),
        )
        return {
            "success":   True,
            "full_text": "\n\n".join(texts),
            "lines":     lines,
            "pages":     max(pages, 1),
            "overlay":   {"lines": all_overlay_lines},
            "error":     None,
        }


# ─── Smart Layout Analyser ────────────────────────────────────────────────────

class SmartLayoutAnalyser:
    """
    Classifies OCR text lines into document structure blocks WITHOUT
    any external AI API. Uses a combination of:

    Signal 1 — Word height from bounding boxes
        OCR.space returns the pixel height of each word.
        Larger text = title/heading. Smaller text = footer/caption.
        We compute the median word height as the "body" baseline,
        then anything 40%+ taller is a heading candidate.

    Signal 2 — Vertical position (Top value)
        Lines at the very top of the page are likely titles.
        Lines at the very bottom are likely footers/page numbers.

    Signal 3 — Line length ratio
        Headings are typically shorter than body paragraphs.
        A line that is <40% of the median line length is a heading candidate.

    Signal 4 — Capitalisation patterns
        ALL CAPS → strong heading signal.
        Title Case (Most Words Capitalised) → heading signal.
        Sentence case → body text.

    Signal 5 — Content patterns (regex)
        "Page N", "N/N", dates → footer.
        "1.", "a)", "•", "-" at start → bullet.
        Numbered/lettered sections → heading.

    Signal 6 — Isolation (blank lines around it)
        A short line surrounded by blank lines = heading or title.

    Signal 7 — Repeated structure
        If the same capitalisation pattern appears multiple times
        at similar positions, it's a consistent heading style.

    All signals are scored and combined — no single rule dominates.
    Falls back gracefully when overlay data is missing.
    """

    # ── Regex helpers ──────────────────────────────────────────────────────────
    _FOOTER_RE  = re.compile(
        r"""
        ^\s*(
            page\s*\d+              |   # Page 1
            \d+\s*/\s*\d+           |   # 1/5
            \d{1,2}[/-]\d{1,2}[/-]\d{2,4}  |  # dates
            \d{4}-\d{2}-\d{2}       |   # ISO date
            (prepared|signed|written|checked)\s+by  |
            confidential            |
            (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}  |
            \d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)
        )\s*$
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _BULLET_RE  = re.compile(r"^(\s*[-\*\u2022\u25cf\u2013]\s+|\s*\d+[.)]\s+|\s*[a-zA-Z][.)]\s+)")

    _HEADING_RE = re.compile(
        r"""
        ^(
            \d+\.\d*\s+[A-Z]        |   # 1.2 Section
            [IVXLCDM]+\.\s+[A-Z]    |   # III. Overview
            [A-Z]\.\s+[A-Z]         |   # A. Background
            #{1,4}\s+               |   # ## Markdown
            chapter\s+\d+           |   # Chapter 1
            section\s+\d+           |   # Section 2
            part\s+[a-z0-9ivx]+         # Part A
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _ONLY_PUNCT = re.compile(r"^[\s\W]+$")

    def analyse(self, lines: list[str], overlay: dict | None = None) -> list[dict[str, str]]:
        """
        Main entry point. Accepts optional overlay dict from OCR.space
        containing per-line bounding box data.
        """
        if not lines:
            return [{"type": "body", "text": "[No text extracted from image]"}]

        # Remove pure punctuation/whitespace lines
        lines = [l for l in lines if not self._ONLY_PUNCT.match(l) and l.strip()]
        if not lines:
            return [{"type": "body", "text": "[No text extracted from image]"}]

        # Build overlay line map: text → bbox metrics
        bbox_map = self._build_bbox_map(overlay)

        # Compute global statistics for relative comparisons
        stats = self._compute_stats(lines, bbox_map)

        # Score and classify every line
        blocks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                blocks.append({"type": "blank", "text": ""})
                continue

            block_type = self._classify_line(
                text    = stripped,
                index   = i,
                total   = len(lines),
                stats   = stats,
                bbox    = bbox_map.get(self._normalise_key(stripped)),
            )
            blocks.append({"type": block_type, "text": stripped})

        # Post-process: merge short body continuations, collapse blank runs
        blocks = self._post_process(blocks)

        # Log summary
        type_counts = Counter(b["type"] for b in blocks)
        logger.info(
            "Layout analysis complete: %d blocks — %s",
            len(blocks),
            ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())),
        )
        return blocks

    # ── BBox helpers ───────────────────────────────────────────────────────────

    def _build_bbox_map(self, overlay: dict | None) -> dict:
        """Build a text → metrics map from OCR.space overlay data."""
        bbox_map = {}
        if not overlay:
            return bbox_map

        for ol_line in overlay.get("lines", []):
            words    = ol_line.get("Words", [])
            if not words:
                continue

            line_text = " ".join(w.get("WordText", "") for w in words).strip()
            if not line_text:
                continue

            heights   = [w.get("Height", 0) for w in words if w.get("Height", 0) > 0]
            tops      = [w.get("Top",    0) for w in words]
            lefts     = [w.get("Left",   0) for w in words]

            bbox_map[self._normalise_key(line_text)] = {
                "avg_height": sum(heights) / len(heights) if heights else 0,
                "max_height": max(heights)  if heights else 0,
                "top":        min(tops),
                "left":       min(lefts),
                "word_count": len(words),
            }
        return bbox_map

    @staticmethod
    def _normalise_key(text: str) -> str:
        """Normalise text for bbox dict lookup."""
        return re.sub(r"\s+", " ", text.strip().lower())

    # ── Statistics ─────────────────────────────────────────────────────────────

    def _compute_stats(self, lines: list[str], bbox_map: dict) -> dict:
        """Compute median/mean values across all lines for relative scoring."""
        lengths  = [len(l.strip()) for l in lines if l.strip()]
        heights  = [
            m["avg_height"]
            for m in bbox_map.values()
            if m["avg_height"] > 0
        ]
        tops     = [
            m["top"]
            for m in bbox_map.values()
            if m.get("top", 0) > 0
        ]

        def median(lst):
            s = sorted(lst)
            n = len(s)
            return s[n // 2] if n else 0

        med_len    = median(lengths) or 40
        med_height = median(heights) or 0
        max_top    = max(tops)   if tops else 0
        min_top    = min(tops)   if tops else 0
        page_height = max_top - min_top if max_top > min_top else 1

        return {
            "med_len":    med_len,
            "med_height": med_height,
            "max_top":    max_top,
            "min_top":    min_top,
            "page_height":page_height,
            "total_lines":len(lines),
        }

    # ── Core classifier ────────────────────────────────────────────────────────

    def _classify_line(
        self,
        text:  str,
        index: int,
        total: int,
        stats: dict,
        bbox:  dict | None,
    ) -> str:
        """
        Score each possible block type and return the winner.
        Higher score = more confident.
        """
        scores = {
            "title":      0.0,
            "heading":    0.0,
            "subheading": 0.0,
            "bullet":     0.0,
            "body":       0.0,
            "footer":     0.0,
        }

        t        = text.strip()
        t_lower  = t.lower()
        length   = len(t)
        words    = t.split()
        n_words  = len(words)

        # ── Signal 1: Word height from bounding boxes ──────────────────────
        if bbox and stats["med_height"] > 0:
            h_ratio = bbox["avg_height"] / stats["med_height"]

            if h_ratio >= 1.6:
                scores["title"]   += 4.0
                scores["heading"] += 2.0
            elif h_ratio >= 1.35:
                scores["heading"]    += 3.5
                scores["subheading"] += 1.5
            elif h_ratio >= 1.15:
                scores["subheading"] += 2.5
                scores["heading"]    += 1.0
            elif h_ratio <= 0.75:
                scores["footer"]  += 3.0
                scores["body"]    += 0.5

        # ── Signal 2: Vertical position ────────────────────────────────────
        if bbox and stats["page_height"] > 0:
            rel_pos = (bbox["top"] - stats["min_top"]) / stats["page_height"]
            if rel_pos <= 0.08:   # top 8% of page
                scores["title"]   += 3.0
                scores["heading"] += 1.0
            elif rel_pos >= 0.92:  # bottom 8% of page
                scores["footer"]  += 3.5

        # ── Signal 3: Line position (index) ────────────────────────────────
        rel_idx = index / max(total - 1, 1)
        if rel_idx <= 0.05 and n_words <= 8:
            scores["title"]   += 2.5
        if rel_idx >= 0.95 and n_words <= 6:
            scores["footer"]  += 2.0

        # ── Signal 4: Line length relative to median ───────────────────────
        len_ratio = length / stats["med_len"] if stats["med_len"] > 0 else 1.0
        if len_ratio <= 0.35 and n_words >= 1:
            scores["title"]      += 1.5
            scores["heading"]    += 1.5
            scores["subheading"] += 1.0
        elif len_ratio <= 0.55:
            scores["heading"]    += 0.8
            scores["subheading"] += 0.8
        elif len_ratio >= 1.4:
            scores["body"]       += 1.5

        # ── Signal 5: Capitalisation pattern ───────────────────────────────
        all_caps  = t == t.upper() and any(c.isalpha() for c in t)
        title_case = (
            n_words >= 2
            and sum(1 for w in words if w and w[0].isupper()) / n_words >= 0.7
            and not all_caps
        )
        sentence_case = (
            t and t[0].isupper()
            and sum(1 for w in words[1:] if w and w[0].isupper()) / max(n_words - 1, 1) <= 0.3
        )

        if all_caps:
            if n_words <= 6:
                scores["title"]   += 3.0
                scores["heading"] += 2.0
            else:
                scores["heading"] += 2.5
        elif title_case:
            if n_words <= 5:
                scores["title"]      += 2.0
                scores["heading"]    += 1.5
            else:
                scores["heading"]    += 1.0
                scores["subheading"] += 0.8
        elif sentence_case and length > 40:
            scores["body"] += 1.0

        # ── Signal 6: Content / regex patterns ─────────────────────────────
        if self._FOOTER_RE.search(t_lower):
            scores["footer"] += 5.0

        if self._BULLET_RE.match(t):
            scores["bullet"] += 5.0

        if self._HEADING_RE.match(t):
            scores["heading"]    += 3.5
            scores["subheading"] += 1.0

        # Explicit structural words
        if any(t_lower.startswith(kw) for kw in
               ["introduction", "conclusion", "summary", "references",
                "abstract", "overview", "background", "objectives",
                "methodology", "results", "discussion", "appendix"]):
            scores["heading"] += 3.0

        # Very short single-word or two-word lines that aren't bullets
        if n_words <= 2 and length <= 20 and not self._BULLET_RE.match(t):
            scores["heading"] += 1.0
            scores["title"]   += 0.5

        # Long prose lines are almost certainly body text
        if n_words >= 12 and length >= 60:
            scores["body"]    += 2.5
            scores["heading"] -= 1.0
            scores["title"]   -= 2.0

        # ── Signal 7: Punctuation at end ───────────────────────────────────
        if t.endswith((".", "?", "!")):
            scores["body"]    += 0.8
            scores["heading"] -= 0.5
            scores["title"]   -= 0.5
        if t.endswith(":"):
            scores["heading"]    += 1.5
            scores["subheading"] += 1.0

        # ── Default body bias ───────────────────────────────────────────────
        scores["body"] += 0.5

        # ── Pick winner ─────────────────────────────────────────────────────
        winner = max(scores, key=scores.get)

        logger.debug(
            "  [%d] %-50s → %-12s  scores=%s",
            index, t[:50], winner,
            {k: round(v, 1) for k, v in sorted(scores.items(), key=lambda x: -x[1])}
        )
        return winner

    # ── Post-processing ────────────────────────────────────────────────────────

    def _post_process(self, blocks: list[dict]) -> list[dict]:
        """
        1. Merge consecutive short body lines into paragraphs.
        2. Collapse multiple blank lines into one.
        3. Re-classify isolated short body lines between headings as subheadings.
        """
        # Step 1: collapse blank runs
        result = []
        for block in blocks:
            if block["type"] == "blank" and result and result[-1]["type"] == "blank":
                continue
            result.append(block)

        # Step 2: merge short body continuation lines
        merged = []
        for block in result:
            if (
                block["type"] == "body"
                and merged
                and merged[-1]["type"] == "body"
                and len(block["text"]) < 55
                and not block["text"][0].isupper()  # likely continuation
            ):
                merged[-1]["text"] += " " + block["text"]
            else:
                merged.append(block)

        # Step 3: isolated short body between two headings → subheading
        for i in range(1, len(merged) - 1):
            prev_t = merged[i - 1]["type"]
            curr   = merged[i]
            next_t = merged[i + 1]["type"]
            if (
                curr["type"] == "body"
                and len(curr["text"].split()) <= 5
                and prev_t in ("heading", "title", "blank")
                and next_t in ("body", "bullet", "blank")
            ):
                merged[i] = {**curr, "type": "subheading"}

        return merged


# ── Keep old name as alias for backwards compatibility ────────────────────────
LayoutAnalyser    = SmartLayoutAnalyser
AILayoutAnalyser  = SmartLayoutAnalyser
