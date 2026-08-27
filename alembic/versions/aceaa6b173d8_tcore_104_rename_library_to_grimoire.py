"""tcore_104_rename_library_to_grimoire

Renames spellcast.library -> spellcast.grimoire and spellcast.spelllibrary ->
spellcast.spellgrimoire in-place (non-destructive, preserves data), including the
spelllibrary.library_id -> spellgrimoire.grimoire_id column and the constraints that
reference the renamed tables. Same rename-in-place strategy as
7ee28eb84e04_tcore_78_rename_document_to_spell.py -- never drop/create.

Constraint names below are INFERRED, not independently verified against the live DB via
pg_constraint (unlike 7ee28eb84e04's author, this revision was written without DB access).
The inference is Postgres's default auto-generated naming for the unnamed constraints
declared in 4056053934a4_tcore_38.py (no custom naming_convention is configured on Base,
confirmed by reading app/models/grimoire.py and both prior migrations), so it should be
correct, but: BEFORE RUNNING THIS MIGRATION, verify the actual names with
`\\d spellcast.library` / `\\d spellcast.spelllibrary` in psql (or query pg_constraint) and
adjust the ALTER TABLE statements below if they differ. If a name is wrong, the ALTER TABLE
fails cleanly with a Postgres error inside this migration's transaction (no partial state,
nothing lost) -- just fix the name and re-run.
  library_pkey                  -> grimoire_pkey
  library_user_id_fkey          -> grimoire_user_id_fkey
  library_user_id_key           -> grimoire_user_id_key   (from UniqueConstraint('user_id'))
  spelllibrary_pkey             -> spellgrimoire_pkey
  spelllibrary_spell_id_fkey    -> spellgrimoire_spell_id_fkey
  spelllibrary_library_id_fkey  -> spellgrimoire_grimoire_id_fkey

Revision ID: aceaa6b173d8
Revises: 7ee28eb84e04
Create Date: 2026-08-27 11:40:30.247764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aceaa6b173d8'
down_revision: Union[str, Sequence[str], None] = '7ee28eb84e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('library', 'grimoire', schema='spellcast')
    op.rename_table('spelllibrary', 'spellgrimoire', schema='spellcast')
    op.alter_column('spellgrimoire', 'library_id', new_column_name='grimoire_id', schema='spellcast')

    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT library_pkey TO grimoire_pkey")
    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT library_user_id_fkey TO grimoire_user_id_fkey")
    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT library_user_id_key TO grimoire_user_id_key")
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spelllibrary_pkey TO spellgrimoire_pkey")
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spelllibrary_spell_id_fkey TO spellgrimoire_spell_id_fkey")
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spelllibrary_library_id_fkey TO spellgrimoire_grimoire_id_fkey")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spellgrimoire_grimoire_id_fkey TO spelllibrary_library_id_fkey")
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spellgrimoire_spell_id_fkey TO spelllibrary_spell_id_fkey")
    op.execute("ALTER TABLE spellcast.spellgrimoire RENAME CONSTRAINT spellgrimoire_pkey TO spelllibrary_pkey")
    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT grimoire_user_id_key TO library_user_id_key")
    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT grimoire_user_id_fkey TO library_user_id_fkey")
    op.execute("ALTER TABLE spellcast.grimoire RENAME CONSTRAINT grimoire_pkey TO library_pkey")

    op.alter_column('spellgrimoire', 'grimoire_id', new_column_name='library_id', schema='spellcast')
    op.rename_table('spellgrimoire', 'spelllibrary', schema='spellcast')
    op.rename_table('grimoire', 'library', schema='spellcast')
