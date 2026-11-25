from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pymupdf as fitz
from docx import Document
from langsmith import traceable


class DocumentError(ValueError):
    pass


@traceable(name="parse_document", run_type="tool")
def parse_document(
    data: bytes, filename: str, max_bytes: int = 10 * 1024 * 1024, max_chars: int = 40000
) -> str:
    """Read entirely in memory; reject scanned, invalid and decompression-heavy files."""
    if not data or len(data) > max_bytes:
        raise DocumentError("Resume is empty or exceeds the upload size limit.")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            if not data.startswith(b"%PDF-"):
                raise DocumentError("The uploaded file is not a PDF.")
            with fitz.open(stream=data, filetype="pdf") as doc:
                if doc.is_encrypted:
                    raise DocumentError("Please upload an unlocked PDF.")
                if len(doc) > 40:
                    raise DocumentError("Resume must contain at most 40 pages.")
                text = "\n".join(page.get_text() for page in doc)
        elif suffix == ".docx":
            with ZipFile(BytesIO(data)) as archive:
                if sum(i.file_size for i in archive.infolist()) > 30 * 1024 * 1024:
                    raise DocumentError("DOCX expanded content exceeds the safe limit.")
                if "word/document.xml" not in archive.namelist():
                    raise DocumentError("The uploaded file is not a Word document.")
            doc = Document(BytesIO(data))
            text = "\n".join(
                [p.text for p in doc.paragraphs]
                + [c.text for t in doc.tables for row in t.rows for c in row.cells]
            )
        else:
            raise DocumentError("Only PDF and DOCX resumes are supported.")
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("Cannot read this document. Re-export it as PDF or DOCX.") from exc
    if len(text.strip()) < 40:
        raise DocumentError("No readable resume text. Scanned PDFs need OCR before upload.")
    if len(text) > max_chars:
        raise DocumentError(f"Resume exceeds the {max_chars:,} character limit.")
    return text.strip()
