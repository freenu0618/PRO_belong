"""add elderly_stats id sequence

Revision ID: 7e1ea3a08c1c
Revises: ce0511dc8a70
Create Date: 2025-11-24 16:48:01.513022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e1ea3a08c1c'
down_revision = 'ce0511dc8a70'
branch_labels = None
depends_on = None



depends_on = None


def upgrade():
    # 1) ELDERLY_STATS_ID_SEQ 시퀀스 생성
    op.execute(
        """
        CREATE SEQUENCE ELDERLY_STATS_ID_SEQ
        START WITH 1
        INCREMENT BY 1
        NOCACHE
        """
    )

    # 2) BEFORE INSERT 트리거 생성
    #    - INSERT 시 ID가 NULL이면 ELDERLY_STATS_ID_SEQ.NEXTVAL로 자동 채움
    conn = op.get_bind()
    conn.exec_driver_sql(
        """
        CREATE OR REPLACE TRIGGER ELDERLY_STATS_BI_TRG
        BEFORE INSERT ON "ELDERLY_STATS"
        FOR EACH ROW
        WHEN (NEW.ID IS NULL)
        BEGIN
          SELECT ELDERLY_STATS_ID_SEQ.NEXTVAL INTO :NEW.ID FROM dual;
        END;
        """
    )


def downgrade():
    # 롤백 시 트리거와 시퀀스 삭제
    conn = op.get_bind()
    conn.exec_driver_sql("DROP TRIGGER ELDERLY_STATS_BI_TRG")
    op.execute("DROP SEQUENCE ELDERLY_STATS_ID_SEQ")