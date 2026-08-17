"""update_user_subscription_fk_to_credentials

Revision ID: becce1dff81d
Revises: bdc3fe32fe29
Create Date: 2026-08-02 22:54:36.335507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'becce1dff81d'
down_revision: Union[str, Sequence[str], None] = 'bdc3fe32fe29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar la Foreign Key antigua que apunta a azure_credentials
    op.drop_constraint(
        'user_subscription_current_credential_fkey', 
        'user_subscription', 
        type_='foreignkey',
        schema='spellcast'  # Remueve el schema si no usas esquemas explícitos
    )
    
    # 2. Crear la nueva Foreign Key apuntando a la tabla genérica 'credential'
    op.create_foreign_key(
        'user_subscription_current_credential_fkey',
        source_table='user_subscription',
        referent_table='credential',
        local_cols=['current_credential'],
        remote_cols=['id'],
        source_schema='spellcast',
        referent_schema='spellcast',
        ondelete='SET NULL'
    )

def downgrade() -> None:
    # Revertir en caso de emergencia
    op.drop_constraint(
        'user_subscription_current_credential_fkey', 
        'user_subscription', 
        type_='foreignkey',
        schema='spellcast'
    )
    op.create_foreign_key(
        'user_subscription_current_credential_fkey',
        source_table='user_subscription',
        referent_table='azure_credentials',
        local_cols=['current_credential'],
        remote_cols=['id'],
        source_schema='spellcast',
        referent_schema='spellcast'
    )