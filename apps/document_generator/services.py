"""
PDF Generator Service.

Each style template produces a visually distinct PDF:

  default  — Helvetica, navy text, underline headings, justified body
  academic — Times Roman, double-spaced, small-caps headings, first-line indent
  notion   — Helvetica, left-bar headings, warm palette, generous spacing
  minimal  — Courier monospace, compact, plain headings
"""

import logging
import re
from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _hex(hex_str: str) -> colors.Color:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return colors.Color(r, g, b)

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}',
    re.IGNORECASE,
)

def _is_uuid(text: str) -> bool:
    t = text.strip()
    if _UUID_RE.match(t): return True
    s = t.replace('-','').replace('_','')
    return len(s) >= 20 and all(c in '0123456789abcdefABCDEF' for c in s)

def _clean_title(title: str) -> str:
    if not title: return ""
    t = re.sub(r'\.(jpg|jpeg|png|gif|bmp|tif|tiff|pdf|webp|heic)$','',
               title.strip(), flags=re.IGNORECASE)
    return "" if _is_uuid(t) else t.strip()

def _esc(text: str) -> str:
    return (text.replace("&","&amp;").replace("<","&lt;")
                .replace(">","&gt;").replace('"',"&quot;"))

def _strip_bullet(text: str) -> str:
    return re.sub(r"^[-\*•→]\s+|^\d+[.)]\s+|^[a-zA-Z][.)]\s+", "", text).strip()


# ─── PDF Generator ────────────────────────────────────────────────────────────

class PDFGenerator:

    def __init__(self, style_name: str = "default"):
        self.style_name = style_name
        tpl = settings.DOCUMENT_STYLE_TEMPLATES.get(
            style_name, settings.DOCUMENT_STYLE_TEMPLATES["default"]
        )
        self.tpl  = tpl

        # Core typography
        self.font      = tpl["font_family"]
        self.fs        = tpl["font_size"]
        self.hs        = tpl["heading_size"]
        self.spacing   = tpl["line_spacing"]
        self.primary   = _hex(tpl["primary_color"])
        self.secondary = _hex(tpl["secondary_color"])

        # Margins
        self.ml = tpl["margin_left"]
        self.mr = tpl["margin_right"]
        self.mt = tpl["margin_top"]
        self.mb = tpl["margin_bottom"]

        # Optional style keys with defaults
        self.border_outer_w  = tpl.get("border_outer_width", 1.2)
        self.border_inner_w  = tpl.get("border_inner_width", 0.5)
        self.border_gap      = tpl.get("border_gap", 4)
        self.heading_style   = tpl.get("heading_style", "underline")
        self.body_alignment  = tpl.get("body_alignment", 4)
        self.body_indent     = tpl.get("body_indent", 0)
        self.bullet_char     = tpl.get("bullet_char", "•")
        self.heading_caps    = tpl.get("heading_caps", False)
        self.subheading_italic = tpl.get("subheading_italic", False)
        self.subheading_color  = _hex(tpl["primary_color"])
        if tpl.get("subheading_color"):
            self.subheading_color = _hex(tpl["subheading_color"])
        self.callout_style   = tpl.get("callout_style", False)
        self.first_para_indent = tpl.get("first_para_indent", True)

        # Bold font name
        self.bold = f"{self.font}-Bold" if self.font not in ("Courier",) else self.font

        # Italic font name
        if self.font == "Times-Roman":
            self.italic = "Times-Italic"
            self.bold_italic = "Times-BoldItalic"
        elif self.font == "Helvetica":
            self.italic = "Helvetica-Oblique"
            self.bold_italic = "Helvetica-BoldOblique"
        else:
            self.italic = self.font
            self.bold_italic = self.font

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(self, blocks, title, customer_id, doc_id) -> str:
        out_dir = Path(settings.OUTPUT_DIR) / str(customer_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"document_{doc_id}.pdf")

        styles    = self._build_styles()
        flowables = self._build_flowables(blocks, styles)
        self._write_pdf(out_path, flowables)

        logger.info("PDF [%s] written: %s", self.style_name, out_path)
        return out_path

    # ── Style Sheets ───────────────────────────────────────────────────────────

    def _build_styles(self) -> dict:
        fs   = self.fs
        hs   = self.hs
        lead = int(fs * self.spacing)

        # ── Title ─────────────────────────────────────────────────────────────
        title_style = ParagraphStyle(
            "DocTitle",
            fontName    = self.bold,
            fontSize    = hs + 8,
            leading     = int((hs + 8) * 1.25),
            textColor   = self.primary,
            spaceAfter  = 10,
            alignment   = 1,    # always centred
        )

        # ── Heading ───────────────────────────────────────────────────────────
        if self.style_name == "academic":
            # Small-caps effect: bold, letter-spaced, same size as body + 2
            heading_style = ParagraphStyle(
                "DocHeading",
                fontName    = self.bold,
                fontSize    = hs,
                leading     = int(hs * 1.4),
                textColor   = self.primary,
                spaceBefore = 20,
                spaceAfter  = 2,
                alignment   = 0,
                textTransform = "uppercase" if self.heading_caps else None,
            )
        elif self.style_name == "notion":
            # Large, dark, left-aligned, bold, more space above
            heading_style = ParagraphStyle(
                "DocHeading",
                fontName    = self.bold,
                fontSize    = hs,
                leading     = int(hs * 1.2),
                textColor   = self.primary,
                spaceBefore = 22,
                spaceAfter  = 6,
                alignment   = 0,
                leftIndent  = 12,    # indent inside the left-bar box
            )
        else:
            heading_style = ParagraphStyle(
                "DocHeading",
                fontName    = self.bold,
                fontSize    = hs,
                leading     = int(hs * 1.3),
                textColor   = self.primary,
                spaceBefore = 14,
                spaceAfter  = 4,
                alignment   = 0,
            )

        # ── Subheading ────────────────────────────────────────────────────────
        if self.style_name == "academic":
            # Italic, slightly smaller than heading
            subheading_style = ParagraphStyle(
                "DocSubHeading",
                fontName    = self.italic,
                fontSize    = fs + 1,
                leading     = int((fs + 1) * 1.5),
                textColor   = self.primary,
                spaceBefore = 10,
                spaceAfter  = 2,
                alignment   = 0,
                leftIndent  = 0,
            )
        elif self.style_name == "notion":
            # Muted grey, regular weight, slightly indented
            subheading_style = ParagraphStyle(
                "DocSubHeading",
                fontName    = self.bold,
                fontSize    = fs + 2,
                leading     = int((fs + 2) * 1.4),
                textColor   = self.subheading_color,
                spaceBefore = 12,
                spaceAfter  = 4,
                alignment   = 0,
                leftIndent  = 16,
            )
        else:
            subheading_style = ParagraphStyle(
                "DocSubHeading",
                fontName    = self.bold,
                fontSize    = fs + 1,
                leading     = int((fs + 1) * 1.4),
                textColor   = self.primary,
                spaceBefore = 8,
                spaceAfter  = 3,
                leftIndent  = 10,
            )

        # ── Body ──────────────────────────────────────────────────────────────
        if self.style_name == "academic":
            # Double-spaced, fully justified, first-line indent
            body_style = ParagraphStyle(
                "DocBody",
                fontName       = self.font,
                fontSize       = fs,
                leading        = lead,
                textColor      = self.primary,
                spaceAfter     = 0,       # no extra space between paras (indent signals new para)
                spaceBefore    = 0,
                alignment      = 4,       # justified
                firstLineIndent= self.body_indent,
            )
        elif self.style_name == "notion":
            # Relaxed, left-aligned, warm dark colour, generous spacing
            body_style = ParagraphStyle(
                "DocBody",
                fontName    = self.font,
                fontSize    = fs,
                leading     = lead,
                textColor   = self.primary,
                spaceAfter  = 8,
                spaceBefore = 0,
                alignment   = 0,          # left-aligned
                leftIndent  = 16 if self.callout_style else 0,
            )
        else:
            body_style = ParagraphStyle(
                "DocBody",
                fontName    = self.font,
                fontSize    = fs,
                leading     = lead,
                textColor   = self.primary,
                spaceAfter  = 6,
                alignment   = self.body_alignment,
                firstLineIndent = self.body_indent,
            )

        # ── Bullet ────────────────────────────────────────────────────────────
        bullet_style = ParagraphStyle(
            "DocBullet",
            fontName    = self.font,
            fontSize    = fs,
            leading     = lead,
            textColor   = self.primary,
            leftIndent  = 20 if self.style_name == "notion" else 12,
            spaceAfter  = 3 if self.style_name == "notion" else 2,
        )

        # ── Footer block ──────────────────────────────────────────────────────
        footer_block_style = ParagraphStyle(
            "DocFooterBlock",
            fontName    = self.italic,
            fontSize    = fs - 1,
            leading     = int((fs - 1) * 1.4),
            textColor   = self.secondary,
            spaceBefore = 6,
            spaceAfter  = 2,
            alignment   = 1,
        )

        return {
            "title":        title_style,
            "heading":      heading_style,
            "subheading":   subheading_style,
            "body":         body_style,
            "bullet_item":  bullet_style,
            "footer_block": footer_block_style,
        }

    # ── Flowable Builder ───────────────────────────────────────────────────────

    def _build_flowables(self, blocks, styles) -> list:
        flowables       = []
        pending_bullets = []
        title_done      = False
        after_heading   = False    # tracks whether next body para follows a heading

        W, H = A4
        content_w = W - self.ml - self.mr

        def flush_bullets():
            if not pending_bullets:
                return
            items = [
                ListItem(
                    Paragraph(_esc(b), styles["bullet_item"]),
                    bulletColor=self.primary,
                    leftIndent=24,
                )
                for b in pending_bullets
            ]
            flowables.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start=self.bullet_char,
                    bulletFontSize=self.fs,
                )
            )
            pending_bullets.clear()

        def add_heading(text):
            """Render a heading according to the template heading_style."""
            nonlocal after_heading
            flush_bullets()

            if self.heading_style == "underline":
                # Bold text + full-width underline rule
                flowables.append(Paragraph(_esc(text), styles["heading"]))
                flowables.append(
                    HRFlowable(
                        width="100%", thickness=1.2,
                        color=self.primary, spaceAfter=6,
                    )
                )

            elif self.heading_style == "leftbar":
                # Notion: coloured left stripe + shaded background band
                bar_color = _hex(self.tpl.get("heading_bar_accent", "#37352F"))
                bg_color  = _hex(self.tpl.get("heading_bar_color",  "#E9E5DD"))

                # Single-cell table gives us background shading + left border
                cell_style = [
                    ("BACKGROUND", (0,0), (-1,-1), bg_color),
                    ("LEFTPADDING",  (0,0), (-1,-1), 14),
                    ("RIGHTPADDING", (0,0), (-1,-1), 8),
                    ("TOPPADDING",   (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 6),
                    ("LINEAFTER",    (0,0), (-1,-1), 0,  colors.white),
                    ("LINEBEFORE",   (0,0), (-1,-1), 4,  bar_color),
                    ("ROWBACKGROUNDS",(0,0),(-1,-1), [bg_color]),
                ]
                t = Table([[Paragraph(_esc(text), styles["heading"])]],
                          colWidths=[content_w])
                t.setStyle(TableStyle(cell_style))
                flowables.append(Spacer(1, 8))
                flowables.append(t)
                flowables.append(Spacer(1, 4))

            elif self.heading_style == "plain":
                # Minimal: heading text only, no decoration
                flowables.append(Paragraph(_esc(text), styles["heading"]))

            else:
                # Default fallback
                flowables.append(Paragraph(_esc(text), styles["heading"]))
                flowables.append(
                    HRFlowable(
                        width="100%", thickness=0.5,
                        color=self.secondary, spaceAfter=4,
                    )
                )

            after_heading = True

        for block in blocks:
            btype = block.get("type", "body")
            text  = block.get("text", "").strip()

            if not text:
                if btype == "blank":
                    flush_bullets()
                    flowables.append(Spacer(1, 4 if self.style_name == "academic" else 6))
                continue

            if btype == "title":
                flush_bullets()
                if not title_done:
                    flowables.append(Paragraph(_esc(text), styles["title"]))
                    # Academic: double line under title
                    if self.style_name == "academic":
                        flowables.append(
                            HRFlowable(width="100%", thickness=1.5,
                                       color=self.primary, spaceAfter=2)
                        )
                        flowables.append(
                            HRFlowable(width="100%", thickness=0.5,
                                       color=self.primary, spaceAfter=14)
                        )
                    # Notion: subtle divider
                    elif self.style_name == "notion":
                        flowables.append(Spacer(1, 4))
                        flowables.append(
                            HRFlowable(width="100%", thickness=0.4,
                                       color=self.secondary, spaceAfter=14)
                        )
                    else:
                        flowables.append(
                            HRFlowable(width="100%", thickness=1.5,
                                       color=self.primary, spaceAfter=12)
                        )
                    title_done = True
                else:
                    add_heading(text)
                after_heading = True

            elif btype == "heading":
                add_heading(text)

            elif btype == "subheading":
                flush_bullets()
                flowables.append(Paragraph(_esc(text), styles["subheading"]))
                if self.style_name == "academic":
                    # Thin rule under subheadings in academic
                    flowables.append(
                        HRFlowable(width="60%", thickness=0.4,
                                   color=self.secondary, spaceAfter=4)
                    )
                after_heading = False

            elif btype == "bullet":
                pending_bullets.append(_strip_bullet(text))
                after_heading = False

            elif btype == "footer":
                flush_bullets()
                flowables.append(Spacer(1, 10))
                flowables.append(
                    HRFlowable(width="100%", thickness=0.3,
                               color=self.secondary, spaceAfter=3)
                )
                flowables.append(Paragraph(_esc(text), styles["footer_block"]))
                after_heading = False

            else:   # body
                flush_bullets()
                # Academic: suppress first-line indent for the first para after a heading
                if (self.style_name == "academic"
                        and after_heading
                        and not self.first_para_indent):
                    no_indent = ParagraphStyle(
                        "DocBodyNoIndent",
                        parent          = styles["body"],
                        firstLineIndent = 0,
                    )
                    flowables.append(Paragraph(_esc(text), no_indent))
                else:
                    flowables.append(Paragraph(_esc(text), styles["body"]))

                # Academic: add inter-paragraph spacing via spacer (not spaceAfter)
                if self.style_name == "academic":
                    flowables.append(Spacer(1, 2))

                after_heading = False

        flush_bullets()
        return flowables

    # ── PDF Assembly ───────────────────────────────────────────────────────────

    def _write_pdf(self, path: str, flowables: list):
        """Build PDF with decorative page border matching the style template."""
        W, H = A4
        BI_OUTER = 18
        BI_INNER = BI_OUTER + self.border_gap

        def on_page(canvas, doc):
            canvas.saveState()

            # Outer border
            canvas.setStrokeColor(self.primary)
            canvas.setLineWidth(self.border_outer_w)
            canvas.rect(BI_OUTER, BI_OUTER,
                        W - 2*BI_OUTER, H - 2*BI_OUTER)

            # Inner border
            canvas.setStrokeColor(self.secondary)
            canvas.setLineWidth(self.border_inner_w)
            canvas.rect(BI_INNER, BI_INNER,
                        W - 2*BI_INNER, H - 2*BI_INNER)

            # Corner decorations — style-specific
            if self.style_name == "academic":
                # Academic: small circles at corners
                canvas.setFillColor(self.primary)
                for cx, cy in [
                    (BI_OUTER, BI_OUTER),
                    (W - BI_OUTER, BI_OUTER),
                    (BI_OUTER, H - BI_OUTER),
                    (W - BI_OUTER, H - BI_OUTER),
                ]:
                    canvas.circle(cx, cy, 3, fill=1, stroke=0)

            elif self.style_name == "notion":
                # Notion: no corner marks — clean minimal border
                pass

            else:
                # Default / minimal: small filled squares
                sq = 4
                canvas.setFillColor(self.primary)
                for cx, cy in [
                    (BI_OUTER, BI_OUTER),
                    (W - BI_OUTER - sq, BI_OUTER),
                    (BI_OUTER, H - BI_OUTER - sq),
                    (W - BI_OUTER - sq, H - BI_OUTER - sq),
                ]:
                    canvas.rect(cx, cy, sq, sq, fill=1, stroke=0)

            # Style name watermark (top-right, very faint)
            canvas.setFillColor(self.secondary)
            canvas.setFont(self.font, 7)
            canvas.setFillAlpha(0.25)
            canvas.drawRightString(
                W - BI_INNER - 4,
                H - BI_INNER - 12,
                self.style_name.upper(),
            )
            canvas.setFillAlpha(1.0)

            # Page number
            canvas.setFont(self.font, 8)
            canvas.setFillColor(self.secondary)
            canvas.drawCentredString(W / 2, BI_INNER + 5, f"— {doc.page} —")

            canvas.restoreState()

        doc = BaseDocTemplate(
            path,
            pagesize     = A4,
            leftMargin   = self.ml,
            rightMargin  = self.mr,
            topMargin    = self.mt,
            bottomMargin = self.mb,
        )

        frame = Frame(
            self.ml, self.mb,
            W - self.ml - self.mr,
            H - self.mt - self.mb,
            id="main",
        )
        doc.addPageTemplates(
            [PageTemplate(id="main", frames=[frame], onPage=on_page)]
        )
        doc.build(flowables)


# ─── Notion HTML Exporter ─────────────────────────────────────────────────────

class NotionHTMLExporter:
    STYLE = """
    <style>
      body{font-family:-apple-system,'Segoe UI',sans-serif;max-width:800px;
           margin:60px auto;color:#37352F;line-height:1.7;padding:0 24px;}
      h1{font-size:2.2em;font-weight:700;margin-bottom:4px;}
      h2{font-size:1.4em;font-weight:600;margin-top:2em;
         border-left:4px solid #37352F;padding-left:12px;
         background:#F5F3EE;padding:6px 12px;}
      h3{font-size:1.1em;font-weight:600;margin-top:1.4em;color:#787774;}
      p{margin:.6em 0;}
      ul{padding-left:1.5em;}
      li{margin:.3em 0;}
      hr{border:none;border-top:1px solid #E9E9E7;margin:1.5em 0;}
      .meta{color:#9B9A97;font-size:.85em;margin-bottom:2em;}
      .footer{color:#9B9A97;font-size:.8em;text-align:center;
              margin-top:2em;border-top:1px solid #E9E9E7;padding-top:8px;}
    </style>"""

    def export(self, blocks, title, created_at=""):
        import html as hl
        clean = _clean_title(title) or "Digitized Document"
        lines = [
            "<!DOCTYPE html><html lang='en'><head>",
            f"<meta charset='UTF-8'><title>{hl.escape(clean)}</title>",
            self.STYLE, "</head><body>",
            f"<h1>{hl.escape(clean)}</h1>",
            f"<p class='meta'>{created_at}</p><hr>",
        ]
        in_list = False
        for b in blocks:
            t = hl.escape(b.get("text",""))
            bt = b.get("type","body")
            if bt=="blank":
                if in_list: lines.append("</ul>"); in_list=False
            elif bt in ("title","heading"):
                if in_list: lines.append("</ul>"); in_list=False
                lines.append(f"<h2>{t}</h2>")
            elif bt=="subheading":
                if in_list: lines.append("</ul>"); in_list=False
                lines.append(f"<h3>{t}</h3>")
            elif bt=="bullet":
                if not in_list: lines.append("<ul>"); in_list=True
                lines.append(f"<li>{hl.escape(_strip_bullet(b.get('text','')))}</li>")
            elif bt=="footer":
                if in_list: lines.append("</ul>"); in_list=False
                lines.append(f"<p class='footer'>{t}</p>")
            else:
                if in_list: lines.append("</ul>"); in_list=False
                lines.append(f"<p>{t}</p>")
        if in_list: lines.append("</ul>")
        lines.append("</body></html>")
        return "\n".join(lines)
