"""Create the four CareerPilot persistence tables."""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_title", sa.String(250), nullable=False),
        sa.Column("company", sa.String(250), nullable=False),
        sa.Column("job_description", sa.Text, nullable=False),
        sa.Column("match_score", sa.Float),
        sa.Column("workflow_status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table in ["resume_profiles", "analysis_results", "applications"]:
        columns = [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "analysis_id",
                sa.String(36),
                sa.ForeignKey("analyses.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
        ]
        if table == "resume_profiles":
            columns += [sa.Column("profile", sa.JSON, nullable=False)]
        elif table == "analysis_results":
            columns += [
                sa.Column("payload", sa.JSON, nullable=False),
                sa.Column("source_text", sa.Text, nullable=False),
            ]
        else:
            columns += [
                sa.Column("status", sa.String(50), nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            ]
        op.create_table(table, *columns)


def downgrade():
    for table in ["applications", "analysis_results", "resume_profiles", "analyses"]:
        op.drop_table(table)
