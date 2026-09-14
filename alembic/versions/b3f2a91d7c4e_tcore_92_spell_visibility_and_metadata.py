"""TCORE-92: spell visibility, transcription lineage, review status and metadata

Add-only migration on spellcast.spell:
- visibility (String, not null, default 'private') -- public | private | shared
- transcribed_from (UUID, nullable, self-FK -> spellcast.spell.id, ON DELETE SET NULL) --
  NULL = root/central spell
- root_spell_id (UUID, nullable, no FK by design) -- denormalized final ancestor of the
  transcription chain; a root spell is its own root_spell_id
- review_status (String, not null, default 'none') -- none | pending | approved | rejected
- description (Text, nullable), author (String, nullable), tags (JSONB, not null,
  default '[]'), language (String, nullable)

Existing rows backfill to the column defaults via server_default (same pattern as
0044117385a8_add_voices_column_to_azure_credentials.py), no manual UPDATE needed.

Revision ID: b3f2a91d7c4e
Revises: aceaa6b173d8
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3f2a91d7c4e'
down_revision: Union[str, Sequence[str], None] = 'aceaa6b173d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('spell', sa.Column('visibility', sa.String(), server_default='private', nullable=False), schema='spellcast')
    op.add_column('spell', sa.Column('transcribed_from', postgresql.UUID(as_uuid=True), nullable=True), schema='spellcast')
    op.add_column('spell', sa.Column('root_spell_id', postgresql.UUID(as_uuid=True), nullable=True), schema='spellcast')
    op.add_column('spell', sa.Column('review_status', sa.String(), server_default='none', nullable=False), schema='spellcast')
    op.add_column('spell', sa.Column('description', sa.Text(), nullable=True), schema='spellcast')
    op.add_column('spell', sa.Column('author', sa.String(), nullable=True), schema='spellcast')
    op.add_column('spell', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False), schema='spellcast')
    op.add_column('spell', sa.Column('language', sa.String(), nullable=True), schema='spellcast')

    op.create_foreign_key(
        'spell_transcribed_from_fkey',
        'spell', 'spell',
        ['transcribed_from'], ['id'],
        source_schema='spellcast', referent_schema='spellcast',
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('spell_transcribed_from_fkey', 'spell', schema='spellcast', type_='foreignkey')

    op.drop_column('spell', 'language', schema='spellcast')
    op.drop_column('spell', 'tags', schema='spellcast')
    op.drop_column('spell', 'author', schema='spellcast')
    op.drop_column('spell', 'description', schema='spellcast')
    op.drop_column('spell', 'review_status', schema='spellcast')
    op.drop_column('spell', 'root_spell_id', schema='spellcast')
    op.drop_column('spell', 'transcribed_from', schema='spellcast')
    op.drop_column('spell', 'visibility', schema='spellcast')
