import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from docx import Document
from docx.oxml.ns import qn

from audit_cross_references import ROLE_LABEL, SUPPLEMENT_POINTERS
from publication_utils import (
    FIGURE_ORDER,
    TABLE_ORDER,
    add_display_math,
    add_rich_text,
    fig,
    figure_filename,
    plain_text,
    tab,
)


def test_display_numbers_follow_registry_order():
    assert [fig(key) for key, _ in FIGURE_ORDER] == [
        f"Figure {index}" for index in range(1, len(FIGURE_ORDER) + 1)
    ]
    assert tab(TABLE_ORDER[-1]) == f"Table {len(TABLE_ORDER)}"
    assert figure_filename("model_sensitivity").startswith("Figure_3_")


def test_rich_text_builds_editable_math_and_superscripts():
    document = Document()
    paragraph = document.add_paragraph()
    add_rich_text(paragraph, "Let $x_{h}^{*}$ be kWh m^{−2}.")
    add_display_math(document, r"x_{c}^{*} = \argmin_{x ∈ X_{c}} L_{c}(x; θ_{c})")
    assert len(document.element.body.findall(".//" + qn("m:oMath"))) == 2
    assert any(run.font.superscript for run in paragraph.runs)
    assert all("$" not in run.text and "\\n" not in run.text for run in paragraph.runs)
    assert plain_text("$x_{inc}$") == "x_inc"


def test_supplement_pointer_detection_ignores_case_role_label():
    assert SUPPLEMENT_POINTERS.search("see Table S2")
    assert SUPPLEMENT_POINTERS.search("in the Supplementary Material")
    assert not SUPPLEMENT_POINTERS.search(
        ROLE_LABEL.sub("", "one supplementary case and one null control")
    )
