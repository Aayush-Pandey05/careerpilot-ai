"""Store voice interview plans, transcripts and feedback."""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_id", sa.String(36), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("turns", sa.JSON(), nullable=False),
        sa.Column("report", sa.JSON(), nullable=True),
    )
    op.create_index("ix_interview_sessions_analysis_id", "interview_sessions", ["analysis_id"])


def downgrade():
    op.drop_index("ix_interview_sessions_analysis_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
