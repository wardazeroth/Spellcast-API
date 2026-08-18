"""tcore_78_rename_document_to_spell

Renames spellcast.document -> spellcast.spell and spellcast.documentlibrary ->
spellcast.spelllibrary in-place (non-destructive, preserves data), including the
documentlibrary.document_id -> spelllibrary.spell_id column and the constraints that
reference the renamed tables. Constraint names below were confirmed against the live DB
via pg_constraint (no custom naming_convention is configured on Base, so these are
Postgres's default auto-generated names for the unnamed constraints in
4056053934a4_tcore_38.py):
  document_pkey                       -> spell_pkey
  documentlibrary_pkey                -> spelllibrary_pkey
  documentlibrary_document_id_fkey    -> spelllibrary_spell_id_fkey
  documentlibrary_library_id_fkey     -> spelllibrary_library_id_fkey

The `library` table itself is untouched (no rename, no column changes).

Revision ID: 7ee28eb84e04
Revises: becce1dff81d
Create Date: 2026-08-18 10:52:34.047348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ee28eb84e04'
down_revision: Union[str, Sequence[str], None] = 'becce1dff81d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('document', 'spell', schema='spellcast')
    op.rename_table('documentlibrary', 'spelllibrary', schema='spellcast')
    op.alter_column('spelllibrary', 'document_id', new_column_name='spell_id', schema='spellcast')

    op.execute("ALTER TABLE spellcast.spell RENAME CONSTRAINT document_pkey TO spell_pkey")
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT documentlibrary_pkey TO spelllibrary_pkey")
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT documentlibrary_document_id_fkey TO spelllibrary_spell_id_fkey")
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT documentlibrary_library_id_fkey TO spelllibrary_library_id_fkey")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT spelllibrary_library_id_fkey TO documentlibrary_library_id_fkey")
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT spelllibrary_spell_id_fkey TO documentlibrary_document_id_fkey")
    op.execute("ALTER TABLE spellcast.spelllibrary RENAME CONSTRAINT spelllibrary_pkey TO documentlibrary_pkey")
    op.execute("ALTER TABLE spellcast.spell RENAME CONSTRAINT spell_pkey TO document_pkey")

    op.alter_column('spelllibrary', 'spell_id', new_column_name='document_id', schema='spellcast')
    op.rename_table('spelllibrary', 'documentlibrary', schema='spellcast')
    op.rename_table('spell', 'document', schema='spellcast')
