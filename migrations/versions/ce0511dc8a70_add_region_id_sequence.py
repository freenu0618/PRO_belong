"""add region id sequence

Revision ID: ce0511dc8a70
Revises: 43bff38566cb
Create Date: 2025-11-24 16:33:05.910049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce0511dc8a70'
down_revision = '43bff38566cb'
branch_labels = None
depends_on = None



def upgrade():
    # 1) 시퀀스 생성
    op.execute(
        """
        CREATE SEQUENCE REGION_ID_SEQ
        START WITH 1
        INCREMENT BY 1
        NOCACHE
        """
    )

    # 2) 트리거 생성 - exec_driver_sql 로 직접 전달 (SQLAlchemy 파싱 방지)
    conn = op.get_bind()
    conn.exec_driver_sql(
        """
        CREATE OR REPLACE TRIGGER REGION_BI_TRG
        BEFORE INSERT ON "REGION"
        FOR EACH ROW
        WHEN (NEW.ID IS NULL)
        BEGIN
          SELECT REGION_ID_SEQ.NEXTVAL INTO :NEW.ID FROM dual;
        END;
        """
    )


def downgrade():
    # 트리거/시퀀스 역순 삭제
    conn = op.get_bind()
    conn.exec_driver_sql("DROP TRIGGER REGION_BI_TRG")
    op.execute("DROP SEQUENCE REGION_ID_SEQ")