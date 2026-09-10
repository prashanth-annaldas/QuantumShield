"""Initial schema migration with all Phase 2-9 tables and indexes

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-09 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=32), server_default='USER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. qds_sessions
    op.create_table(
        'qds_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('sender_id', sa.String(length=64), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_hash', sa.String(length=64), nullable=False),
        sa.Column('nonce', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('verification_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_qds_sessions_session_id', 'qds_sessions', ['session_id'], unique=True)

    # 3. verification_results
    op.create_table(
        'verification_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('qds_session_id', sa.String(length=64), nullable=False),
        sa.Column('fidelity', sa.Float(), nullable=False),
        sa.Column('qber', sa.Float(), nullable=False),
        sa.Column('mismatch_rate', sa.Float(), nullable=False),
        sa.Column('statistical_deviation', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('forgery_probability', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('verification_accuracy', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['qds_session_id'], ['qds_sessions.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_verification_results_session_id', 'verification_results', ['qds_session_id'], unique=False)

    # 4. threat_logs
    op.create_table(
        'threat_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('qds_session_id', sa.String(length=64), nullable=False),
        sa.Column('attack_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('qber_percent', sa.Float(), nullable=False),
        sa.Column('state_fidelity', sa.Float(), nullable=False),
        sa.Column('mismatch_rate', sa.Float(), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['qds_session_id'], ['qds_sessions.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_threat_logs_session_id', 'threat_logs', ['qds_session_id'], unique=False)

    # 5. security_events
    op.create_table(
        'security_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_security_events_event_id', 'security_events', ['event_id'], unique=True)
    op.create_index('ix_security_events_type', 'security_events', ['event_type'], unique=False)
    op.create_index('ix_security_events_created', 'security_events', ['created_at'], unique=False)

    # 6. incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('incident_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incidents_incident_id', 'incidents', ['incident_id'], unique=True)
    op.create_index('ix_incidents_status', 'incidents', ['status'], unique=False)
    op.create_index('ix_incidents_severity', 'incidents', ['severity'], unique=False)

    # 7. audit_logs (Phase 9)
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('actor_role', sa.String(length=32), nullable=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=True),
        sa.Column('resource_id', sa.String(length=64), nullable=True),
        sa.Column('outcome', sa.String(length=32), server_default='SUCCESS', nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='INFO', nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_event_id', 'audit_logs', ['event_id'], unique=True)
    op.create_index('ix_audit_logs_request_id', 'audit_logs', ['request_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_severity', 'audit_logs', ['severity'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('incidents')
    op.drop_table('security_events')
    op.drop_table('threat_logs')
    op.drop_table('verification_results')
    op.drop_table('qds_sessions')
    op.drop_table('users')
