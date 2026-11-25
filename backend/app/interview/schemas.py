from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MIN_MAIN_QUESTIONS = 10
MAX_MAIN_QUESTIONS = 14


class InterviewSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Question(InterviewSchema):
    question: str = Field(min_length=1, max_length=400)
    topic: str = Field(min_length=1, max_length=100)
    kind: Literal["technical", "project", "behavioral", "skill_gap"]
    expected_concepts: list[str] = Field(min_length=1, max_length=5)


class QuestionPlan(InterviewSchema):
    questions: list[Question] = Field(min_length=MIN_MAIN_QUESTIONS, max_length=MAX_MAIN_QUESTIONS)


class NextTurn(InterviewSchema):
    follow_up: str = Field(max_length=400)
    next_question: str = Field(max_length=400)


class Answer(InterviewSchema):
    version: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=4000)


class QuestionFeedback(InterviewSchema):
    number: int = Field(ge=1, le=MAX_MAIN_QUESTIONS)
    rating: int = Field(ge=1, le=4)
    evidence: str
    strength: str
    improvement: str


class InterviewReport(InterviewSchema):
    summary: str
    feedback: list[QuestionFeedback] = Field(min_length=MIN_MAIN_QUESTIONS, max_length=MAX_MAIN_QUESTIONS)
    practice_tasks: list[str] = Field(min_length=1, max_length=5)
