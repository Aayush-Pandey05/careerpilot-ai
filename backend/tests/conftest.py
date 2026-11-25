import asyncio
import os
from io import BytesIO

import pymupdf as fitz
import pytest
from docx import Document

from app.core.config import Settings
from app.services.llm_service import LLMService

RESUME = """Aarav Mehta
aarav@example.test
Education
BTech Computer Science, Meridian Institute, graduating 2027
Skills
Python, SQL, pandas, scikit-learn, Git, PyTorch
Basic Docker knowledge
Projects
Built a Python sentiment classification project using pandas and scikit-learn.
Experience
Campus research intern: prepared datasets with Python.
Certifications
Introduction to Machine Learning, 2026
"""
JOB = """Title: AI/ML Intern
Company: Northstar Labs
Required skills:
Python, SQL, pandas, scikit-learn, Git
Preferred skills:
Docker, AWS, TensorFlow
Responsibilities:
Build and evaluate machine learning models.
"""


@pytest.fixture
def settings():
    return Settings(_env_file=None, llm_mode="mock", langsmith_tracing=False)


@pytest.fixture
def llm(settings):
    return LLMService(settings)


@pytest.fixture
def resume_text():
    return RESUME


@pytest.fixture
def job_text():
    return JOB


def pdf_bytes(text=RESUME):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(45, 45, 550, 800), text, fontsize=11)
    result = doc.tobytes()
    doc.close()
    return result


def docx_bytes(text=RESUME):
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    output = BytesIO()
    doc.save(output)
    return output.getvalue()


def run(coroutine):
    return asyncio.run(coroutine)


@pytest.fixture
def pg_session():
    """No SQLite replacement. Use an isolated PostgreSQL schema and roll it back."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run real PostgreSQL integration tests.")
    from uuid import uuid4

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from app.database.models import Base

    engine = create_engine(url)
    schema = "test_" + uuid4().hex
    with engine.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA {schema}"))
        connection.execute(text(f"SET search_path TO {schema}"))
        Base.metadata.create_all(connection)
        connection.commit()
        transaction = connection.begin()
        with Session(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as session:
            yield session
        transaction.rollback()
        connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        connection.commit()
    engine.dispose()
