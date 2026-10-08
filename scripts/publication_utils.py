import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "outputs"
FIGURE_ORDER = (
    ("audit_framework", "Legacy Standard Audit"),
    ("primary_case_benchmarks", "Primary-case benchmarks"),
    ("model_sensitivity", "Pre-specified model sensitivity"),
    ("case_classifications", "Frozen-case audit-state matrix"),
)
TABLE_ORDER = (
    "audit_framework",
    "case_design",
    "case_results",
    "falsification",
)
BLACK = RGBColor(0, 0, 0)


def figure_number(key: str) -> int:
    return [name for name, _ in FIGURE_ORDER].index(key) + 1


def table_number(key: str) -> int:
    return TABLE_ORDER.index(key) + 1


def fig(key: str) -> str:
    return f"Figure {figure_number(key)}"


def tab(key: str) -> str:
    return f"Table {table_number(key)}"


def figure_filename(key: str) -> str:
    return f"Figure_{figure_number(key)}_{key}.png"


def table_filename(key: str) -> str:
    return f"Table_{table_number(key)}_{key}.csv"


def load_values() -> dict[str, dict[str, str]]:
    with (PROJECT / "MANUSCRIPT_VALUES.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        return {row["value_id"]: row for row in csv.DictReader(handle)}


def load_results() -> dict[str, dict[str, object]]:
    payload = json.loads(
        (OUTPUT / "analysis" / "case_results.json").read_text(encoding="utf-8")
    )
    return {
        str(result["case_id"]): result for result in payload["case_results"]
    }


def numeric(values: dict[str, dict[str, str]], value_id: str) -> float:
    return float(values[value_id]["estimate"])


def display(values: dict[str, dict[str, str]], value_id: str) -> str:
    row = values[value_id]
    estimate = row["estimate"]
    spec = row["format_spec"]
    if spec == "s":
        return estimate.replace("_", " ")
    number = float(estimate)
    if spec.endswith("%"):
        return format(number, spec)
    if spec.endswith("d"):
        return format(int(round(number)), spec)
    return format(number, spec)


NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
)


def sentence_number(count: int) -> str:
    """Render a count that opens a sentence without a leading numeral."""
    if 0 <= count < len(NUMBER_WORDS):
        return NUMBER_WORDS[count].capitalize()
    return f"A total of {count}"


def interval(values: dict[str, dict[str, str]], value_id: str) -> str:
    row = values[value_id]
    spec = row["format_spec"]
    lower = float(row["lower"])
    upper = float(row["upper"])
    return f"{format(lower, spec)}–{format(upper, spec)}"


def configured_document() -> Document:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.font.color.rgb = BLACK
    for name, size in [("Title", 16), ("Heading 1", 14), ("Heading 2", 12)]:
        style = styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.italic = False
        style.font.color.rgb = BLACK
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        for attribute in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            style._element.rPr.rFonts.attrib.pop(qn(attribute), None)
    caption = styles["Caption"]
    caption.font.name = "Times New Roman"
    caption.font.size = Pt(10)
    caption.font.bold = False
    caption.font.italic = False
    caption.font.color.rgb = BLACK
    caption.paragraph_format.line_spacing = 1.0
    caption.paragraph_format.space_after = Pt(6)
    return document


def add_page_number(document: Document) -> None:
    paragraph = document.sections[0].footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    field_begin = OxmlElement("w:fldChar")
    field_begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = "PAGE"
    field_end = OxmlElement("w:fldChar")
    field_end.set(qn("w:fldCharType"), "end")
    run._r.extend([field_begin, instruction, field_end])


def shade_cell(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_text(cell, text: object, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(9)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_caption(document: Document, caption: str, keep_with_next: bool = False) -> None:
    label, _, text = caption.partition(". ")
    paragraph = document.add_paragraph(style="Caption")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.keep_with_next = keep_with_next
    paragraph.add_run(f"{label}.").bold = True
    if text:
        paragraph.add_run(f" {text}")


def add_table(
    document: Document,
    headers: list[str],
    rows: list[list[object]],
    caption: str,
    widths: list[float] | None = None,
) -> None:
    add_caption(document, caption, keep_with_next=True)
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = widths is None
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True)
        shade_cell(table.rows[0].cells[index], "D9EAF7")
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value)
    for row in table.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if widths:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)
    document.add_paragraph()


def add_figure(
    document: Document,
    image_path: Path,
    caption: str,
    width_inches: float = 6.4,
) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image_path), width=Inches(width_inches))
    paragraph.paragraph_format.keep_with_next = True
    add_caption(document, caption)


def add_landscape_section(document: Document):
    section = document.add_section(WD_SECTION.NEW_PAGE)
    section.orientation = 1
    section.page_width, section.page_height = section.page_height, section.page_width
    return section


def _math_element(tag: str, *children):
    element = OxmlElement(f"m:{tag}")
    for child in children:
        element.append(child)
    return element


def _math_run(text: str, plain: bool = False):
    run = _math_element("r")
    if plain:
        properties = _math_element("rPr")
        style = OxmlElement("m:sty")
        style.set(qn("m:val"), "p")
        properties.append(style)
        run.append(properties)
    word_properties = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Cambria Math")
    fonts.set(qn("w:hAnsi"), "Cambria Math")
    word_properties.append(fonts)
    run.append(word_properties)
    text_element = OxmlElement("m:t")
    text_element.set(qn("xml:space"), "preserve")
    text_element.text = text.replace("*", "\u2217")
    run.append(text_element)
    return run


def _parse_math(source: str, index: int = 0, stop: str | None = None):
    """Parse a small LaTeX-like subset (_{...}, ^{...}, \\argmin_{...}) into OMML."""
    nodes = []
    buffer = ""

    def flush():
        nonlocal buffer
        if buffer:
            nodes.append(_math_run(buffer))
            buffer = ""

    def argument(position: int):
        if source[position] == "{":
            children, position = _parse_math(source, position + 1, "}")
            return children, position + 1
        return [_math_run(source[position])], position + 1

    while index < len(source):
        character = source[index]
        if stop and character == stop:
            break
        if source.startswith("\\argmin", index):
            flush()
            index += len("\\argmin")
            limit = []
            if index < len(source) and source[index] == "_":
                limit, index = argument(index + 1)
            nodes.append(
                _math_element(
                    "limLow",
                    _math_element("e", _math_run("arg min", plain=True)),
                    _math_element("lim", *limit),
                )
            )
            continue
        if character in "_^":
            base_text = buffer[-1:] if buffer else ""
            buffer = buffer[:-1]
            flush()
            base = [_math_run(base_text)] if base_text else ([nodes.pop()] if nodes else [])
            first, index = argument(index + 1)
            if character == "_" and index < len(source) and source[index] == "^":
                second, index = argument(index + 1)
                nodes.append(
                    _math_element(
                        "sSubSup",
                        _math_element("e", *base),
                        _math_element("sub", *first),
                        _math_element("sup", *second),
                    )
                )
            else:
                tag, part = ("sSub", "sub") if character == "_" else ("sSup", "sup")
                nodes.append(
                    _math_element(tag, _math_element("e", *base), _math_element(part, *first))
                )
            continue
        if character == " ":
            index += 1
            continue
        buffer += character
        index += 1
    flush()
    return nodes, index


def add_inline_math(paragraph, expression: str) -> None:
    nodes, _ = _parse_math(expression)
    paragraph._p.append(_math_element("oMath", *nodes))


def add_display_math(document: Document, expression: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nodes, _ = _parse_math(expression)
    paragraph._p.append(_math_element("oMathPara", _math_element("oMath", *nodes)))


def add_rich_text(paragraph, text: str) -> None:
    """Append text where $...$ is OMML math and ^{...} outside math is a superscript."""
    for position, segment in enumerate(text.split("$")):
        if position % 2:
            add_inline_math(paragraph, segment)
            continue
        while "^{" in segment:
            before, _, rest = segment.partition("^{")
            superscript, _, segment = rest.partition("}")
            if before:
                paragraph.add_run(before)
            paragraph.add_run(superscript).font.superscript = True
        if segment:
            paragraph.add_run(segment)


def plain_text(text: str) -> str:
    """Render rich-text markup as plain text for audits and non-Word outputs."""
    output = text.replace("$", "").replace("\\argmin", "arg min")
    return output.replace("^{", "").replace("_{", "_").replace("{", "").replace("}", "")
