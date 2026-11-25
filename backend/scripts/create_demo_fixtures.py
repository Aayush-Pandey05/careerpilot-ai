"""Generate synthetic fixtures for uploads and classroom demonstrations."""

from pathlib import Path

from tests.conftest import JOB, RESUME, docx_bytes, pdf_bytes


def main():
    root = Path(__file__).resolve().parents[2]
    for folder in [root / "backend/tests/fixtures", root / "frontend/public"]:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sample_resume.pdf").write_bytes(pdf_bytes())
        (folder / "sample_resume.docx").write_bytes(docx_bytes())
    (root / "backend/tests/fixtures/sample_job_description.txt").write_text(JOB, encoding="utf-8")
    (root / "backend/tests/fixtures/sample_resume.txt").write_text(RESUME, encoding="utf-8")
    print("Synthetic resume PDF, DOCX and job description created.")


if __name__ == "__main__":
    main()
