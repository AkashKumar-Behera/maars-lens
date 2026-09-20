"""add inspection_images table

Revision ID: 002_add_inspection_images
Revises: 
Create Date: 2026-09-19 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002_add_inspection_images'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create inspection_images table
    op.create_table(
        'inspection_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('panel_type', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('mime', sa.String(length=100), nullable=False, server_default='image/jpeg'),
        sa.Column('size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('original', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('parent_image_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspection_images.id', ondelete='CASCADE'), nullable=True),
    )

    # 2. Make image_storage_path nullable on inspections to support multi-image without requiring legacy single-path
    with op.batch_alter_table('inspections') as batch_op:
        batch_op.alter_column('image_storage_path', existing_type=sa.String(), nullable=True)

    # 3. Data migration: Migrate existing image_storage_path rows into inspection_images
    op.execute("""
        INSERT INTO inspection_images (id, inspection_id, panel_type, storage_path, sha256, mime, size, uploaded_by, uploaded_at, original)
        SELECT 
            COALESCE(uuid_generate_v4(), id), 
            id, 
            'front', 
            image_storage_path, 
            '0000000000000000000000000000000000000000000000000000000000000000', 
            'image/jpeg', 
            0, 
            officer_id, 
            created_at, 
            true
        FROM inspections
        WHERE image_storage_path IS NOT NULL AND image_storage_path != ''
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    # 1. Drop table inspection_images
    op.drop_table('inspection_images')

    # 2. Revert image_storage_path nullable
    with op.batch_alter_table('inspections') as batch_op:
        batch_op.alter_column('image_storage_path', existing_type=sa.String(), nullable=False)
