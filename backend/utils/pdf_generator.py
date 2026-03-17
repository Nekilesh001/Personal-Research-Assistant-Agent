"""
PDF report generator using fpdf2.
Handles Unicode characters and proper layout.
"""

import re
from fpdf import FPDF
from utils.logger import get_logger

logger = get_logger(__name__)


def _sanitize(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2012": "-",
        "\u2011": "-",
        "\u2010": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
        "\u2023": "*",
        "\u25cf": "*",
        "\u25cb": "o",
        "\u2026": "...",
        "\u00a0": " ",
        "\u2192": "->",
        "\u2190": "<-",
        "\u00b7": "*",
        "\u00d7": "x",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u2260": "!=",
        "\u00b1": "+/-",
        "\u00b2": "^2",
        "\u00b3": "^3",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


class ResearchReportPDF(FPDF):
    def __init__(self, title="Research Report"):
        super().__init__()
        self.report_title = _sanitize(title)
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(120, 120, 120)
        safe = self.report_title[:70]
        self.cell(0, 7, f"Research Report  |  {safe}",
                  align="L",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(210, 210, 210)
        self.line(self.l_margin, self.get_y(),
                  self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}",
                  align="C")


def generate_pdf_bytes(markdown_text: str) -> bytes:
    logger.info("pdf_generation_start",
                text_length=len(markdown_text))

    title = "Research Report"
    for line in markdown_text.split("\n"):
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            break

    pdf = ResearchReportPDF(title=title)
    pdf.add_page()

    def clean(text):
        text = _sanitize(text)
        text = re.sub(r"\[(.+?)\]\((.+?)\)",
                      r"\1 (\2)", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        return text.strip()

    usable_width = pdf.w - pdf.l_margin - pdf.r_margin

    for raw_line in markdown_text.split("\n"):
        line = raw_line.rstrip()

        if re.match(r"^-{3,}$", line):
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, pdf.get_y() + 2,
                     pdf.w - pdf.r_margin,
                     pdf.get_y() + 2)
            pdf.ln(6)
            continue

        if line.startswith("# "):
            t = clean(line[2:])
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(usable_width, 9, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            pdf.ln(2)
            continue

        if line.startswith("## "):
            t = clean(line[3:])
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 60, 160)
            pdf.multi_cell(usable_width, 8, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            pdf.set_draw_color(30, 60, 160)
            pdf.line(pdf.l_margin, pdf.get_y(),
                     pdf.w - pdf.r_margin,
                     pdf.get_y())
            pdf.ln(3)
            continue

        if line.startswith("### "):
            t = clean(line[4:])
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(usable_width, 7, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            pdf.ln(1)
            continue

        if line.startswith("> "):
            t = clean(line[2:])
            pdf.set_x(pdf.l_margin + 6)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(usable_width - 6, 6, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            pdf.ln(1)
            continue

        if re.match(r"^[-*+]\s+", line):
            t = clean(re.sub(r"^[-*+]\s+", "", line))
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(4, 6, "-",
                     new_x="RIGHT", new_y="TOP")
            pdf.multi_cell(usable_width - 8, 6, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            continue

        m = re.match(r"^(\d+)\.\s+(.+)", line)
        if m:
            t = clean(m.group(2))
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            num_w = pdf.get_string_width(
                f"{m.group(1)}. ") + 2
            pdf.cell(num_w, 6,
                     f"{m.group(1)}.",
                     new_x="RIGHT", new_y="TOP")
            pdf.multi_cell(usable_width - num_w - 4,
                           6, t,
                           new_x="LMARGIN",
                           new_y="NEXT")
            continue

        if not line.strip():
            pdf.ln(3)
            continue

        t = clean(line)
        if t:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(usable_width, 6, t,
                           new_x="LMARGIN",
                           new_y="NEXT")

    logger.info("pdf_generation_success",
                pages=pdf.page)
    return bytes(pdf.output())
