"""add_missing_tenant_and_status_columns

Revision ID: 88d93b9042c3
Revises: fe1fdc7c11b7
Create Date: 2026-02-12 19:18:35.669588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88d93b9042c3'
down_revision: Union[str, Sequence[str], None] = 'fe1fdc7c11b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing tenant_id, status, and audit columns."""
    # Add tenant_id to existing tables
    op.add_column('users', sa.Column('tenant_id', sa.String(length=100), nullable=True))
    op.add_column('prescriptions', sa.Column('tenant_id', sa.String(length=100), nullable=True))
    op.add_column('dispensings', sa.Column('tenant_id', sa.String(length=100), nullable=True))
    op.add_column('audit_log', sa.Column('tenant_id', sa.String(length=100), nullable=True))
    
    # Add status to prescriptions
    op.add_column('prescriptions', sa.Column('status', sa.String(length=50), nullable=True))
    
    # Add advanced audit columns to audit_log
    op.add_column('audit_log', sa.Column('correlation_id', sa.String(length=100), nullable=True))
    op.add_column('audit_log', sa.Column('session_id', sa.String(length=100), nullable=True))
    op.add_column('audit_log', sa.Column('result', sa.String(length=50), nullable=True))
    op.add_column('audit_log', sa.Column('previous_hash', sa.String(length=256), nullable=True))
    
    # Create index on tenant_id for performance
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_prescriptions_tenant_id', 'prescriptions', ['tenant_id'])


def downgrade() -> None:
    """Remove tenant_id, status, and audit columns."""
    op.drop_index('ix_prescriptions_tenant_id', table_name='prescriptions')
    op.drop_index('ix_users_tenant_id', table_name='users')
    
    # Remove audit columns
    op.drop_column('audit_log', 'previous_hash')
    op.drop_column('audit_log', 'result')
    op.drop_column('audit_log', 'session_id')
    op.drop_column('audit_log', 'correlation_id')
    
    # Remove tenant_id and status
    op.drop_column('prescriptions', 'status')
    op.drop_column('audit_log', 'tenant_id')
    op.drop_column('dispensings', 'tenant_id')
    op.drop_column('prescriptions', 'tenant_id')
    op.drop_column('users', 'tenant_id')
