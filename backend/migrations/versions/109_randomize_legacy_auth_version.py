"""Give users still on the backfilled auth_version '0' a random one.

097 backfilled every existing user with the literal '0', so on an upgraded
install anyone holding the JWT signing key could mint a valid session
without also guessing the per-user epoch that fresh installs get. Each such
user gets a random epoch; their current sessions end and they log in again.
"""
import secrets

import sqlalchemy as sa
from alembic import op

revision = '109_randomize_legacy_auth_version'
down_revision = '108_drop_webhook_zero_downtime'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    users = sa.table('users', sa.column('id', sa.Integer),
                     sa.column('auth_version', sa.String(32)))
    legacy = bind.execute(
        sa.select(users.c.id).where(sa.or_(users.c.auth_version.is_(None),
                                           users.c.auth_version.in_(['0', ''])))
    ).scalars().all()
    for user_id in legacy:
        bind.execute(users.update().where(users.c.id == user_id)
                     .values(auth_version=secrets.token_hex(16)))


def downgrade():
    pass  # a random epoch is valid under the old code too
