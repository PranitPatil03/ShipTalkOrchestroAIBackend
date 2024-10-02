"""added likes

Revision ID: e8ff86fddfba
Revises: fece4107e809
Create Date: 2024-09-21 21:04:49.989044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8ff86fddfba'
down_revision: Union[str, None] = 'fece4107e809'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Posts', sa.Column('likes', sa.Integer(), server_default='0', nullable=True))
    op.drop_column('Posts', 'category2')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Posts', sa.Column('category2', sa.VARCHAR(), server_default=sa.text("'Carrier Comparison'::character varying"), autoincrement=False, nullable=True))
    op.drop_column('Posts', 'likes')
    # ### end Alembic commands ###