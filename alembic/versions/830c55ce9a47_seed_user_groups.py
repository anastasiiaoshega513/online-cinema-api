"""seed user groups

Revision ID: 830c55ce9a47
Revises: db81f74d1e48
Create Date: 2026-05-05 17:28:40.721741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '830c55ce9a47'
down_revision: Union[str, Sequence[str], None] = 'db81f74d1e48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO user_groups (name)
        VALUES ('USER'), ('MODERATOR'), ('ADMIN')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM user_groups
        WHERE name IN ('USER', 'MODERATOR', 'ADMIN')
        """
    )