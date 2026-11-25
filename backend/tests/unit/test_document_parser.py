import pymupdf as fitz
import pytest

from app.tools.document_parser import DocumentError, parse_document
from tests.conftest import docx_bytes, pdf_bytes


@pytest.mark.parametrize("name,builder", [("resume.pdf", pdf_bytes), ("resume.docx", docx_bytes)])
def test_parses_source_documents(name, builder):
    text = parse_document(builder(), name)
    assert "Aarav Mehta" in text and "scikit-learn" in text and "Meridian" in text


@pytest.mark.parametrize(
    "data,name", [(b"bad", "x.pdf"), (b"bad", "x.docx"), (b"bad", "x.exe"), (b"", "x.pdf")]
)
def test_rejects_invalid_documents(data, name):
    with pytest.raises(DocumentError):
        parse_document(data, name)


def test_scanned_or_empty_pdf():
    doc = fitz.open()
    doc.new_page()
    with pytest.raises(DocumentError, match="OCR"):
        parse_document(doc.tobytes(), "scanned.pdf")


def test_size_and_text_limits():
    with pytest.raises(DocumentError, match="size limit"):
        parse_document(pdf_bytes(), "resume.pdf", max_bytes=10)
    with pytest.raises(DocumentError, match="character limit"):
        parse_document(pdf_bytes(), "resume.pdf", max_chars=20)
