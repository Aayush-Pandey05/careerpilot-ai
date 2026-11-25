import operator
from typing import Annotated, TypedDict


class WorkflowState(TypedDict, total=False):
    file_bytes: bytes
    filename: str
    resume_text: str
    job_description: str
    job_title: str
    company: str
    resume: dict
    job: dict
    matching: dict
    application: dict
    review: dict
    revision_count: int
    workflow_status: str
    errors: Annotated[list[str], operator.add]
    events: Annotated[list[dict], operator.add]
