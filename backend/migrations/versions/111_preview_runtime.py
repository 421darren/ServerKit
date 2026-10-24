"""Track preview-owned resources and opt-in environment inheritance."""
import sqlalchemy as sa
from alembic import op

revision = '111_preview_runtime'
down_revision = '110_drop_workflow_schedules_job'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing = {c['name'] for c in inspector.get_columns('application_previews')}
    for name, kind in [('request_token', sa.String(32)), ('requested_action', sa.String(16)),
                       ('runtime_state', sa.Text()), ('error_message', sa.Text())]:
        if name not in existing:
            op.add_column('application_previews', sa.Column(name, kind, nullable=True))
    existing = {c['name'] for c in inspector.get_columns('application_preview_settings')}
    if 'inherit_environment' not in existing:
        op.add_column('application_preview_settings', sa.Column(
            'inherit_environment', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('application_preview_settings') as batch:
        batch.drop_column('inherit_environment')
    with op.batch_alter_table('application_previews') as batch:
        batch.drop_column('request_token')
        batch.drop_column('requested_action')
        batch.drop_column('error_message')
        batch.drop_column('runtime_state')
