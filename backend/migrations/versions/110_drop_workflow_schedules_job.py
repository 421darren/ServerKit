"""Drop the retired workflow-schedules periodic job.

Its handler became a no-op when the workflow engine was retired, yet the
schedule kept firing every 60 seconds — about 1,440 empty job rows a day.
The handler is gone, so the row goes too; any job still queued for it is
cancelled rather than failing with "no handler registered".
"""
import sqlalchemy as sa
from alembic import op

revision = '110_drop_workflow_schedules_job'
down_revision = '109_randomize_legacy_auth_version'
branch_labels = None
depends_on = None

KIND = 'builtin.workflow_schedules'


def upgrade():
    bind = op.get_bind()
    scheduled = sa.table('scheduled_jobs', sa.column('name', sa.String))
    jobs = sa.table('jobs', sa.column('kind', sa.String), sa.column('status', sa.String))
    bind.execute(scheduled.delete().where(scheduled.c.name == 'workflow-schedules'))
    bind.execute(jobs.update()
                 .where(jobs.c.kind == KIND, jobs.c.status == 'pending')
                 .values(status='cancelled'))


def downgrade():
    # Nothing to restore: the handler no longer exists.
    pass
