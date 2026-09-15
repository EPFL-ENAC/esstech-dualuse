"""convert comparison_set_case inclusion_reason to enum

Revision ID: f527b60e072a
Revises: d212d050cd65
Create Date: 2026-09-15 15:17:55.369910

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f527b60e072a'
down_revision: Union[str, None] = 'd212d050cd65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Not auto-detected: alembic's autogenerate does not compare the CHECK
    # constraint implied by an unnamed Enum(native_enum=False) column
    # against a plain String column, so this migration is hand-written.
    # Backfill before constraining: comparison_set_case already has real
    # rows in the dev database storing the old free-text values.
    op.execute(
        "UPDATE comparison_set_case SET inclusion_reason = 'shared_function' "
        "WHERE inclusion_reason = 'shared function'"
    )
    op.execute(
        "UPDATE comparison_set_case SET inclusion_reason = 'widened_by_domain' "
        "WHERE inclusion_reason = 'widened by domain'"
    )
    op.create_check_constraint(
        'ck_comparison_set_case_inclusion_reason',
        'comparison_set_case',
        "inclusion_reason IN ('shared_function', 'widened_by_domain')",
    )


def downgrade() -> None:
    op.drop_constraint(
        'ck_comparison_set_case_inclusion_reason',
        'comparison_set_case',
        type_='check',
    )
    op.execute(
        "UPDATE comparison_set_case SET inclusion_reason = 'shared function' "
        "WHERE inclusion_reason = 'shared_function'"
    )
    op.execute(
        "UPDATE comparison_set_case SET inclusion_reason = 'widened by domain' "
        "WHERE inclusion_reason = 'widened_by_domain'"
    )
