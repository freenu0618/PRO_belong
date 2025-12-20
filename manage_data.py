import os
import sys
import pandas as pd
from sqlalchemy import text
from belong.app import create_app, db

# 백업 파일이 저장될 경로 (RunPod 영구 볼륨)
BACKUP_DIR = "/workspace/backup_data"

def backup():
    """DB의 모든 테이블을 JSON 파일로 백업합니다."""
    app = create_app()
    with app.app_context():
        print(f"🚀 Starting Backup to {BACKUP_DIR}...")
        
        # 디렉토리 생성
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # 테이블 목록 조회
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            try:
                print(f"📦 Backing up table: {table}")
                df = pd.read_sql_table(table, db.engine)
                # 날짜 형식 보존을 위해 iso_dates=True
                df.to_json(f"{BACKUP_DIR}/{table}.json", orient="records", date_format="iso", force_ascii=False)
                print(f"✅ Saved {len(df)} rows.")
            except Exception as e:
                print(f"❌ Failed to backup {table}: {e}")
                
        print("🎉 Backup Complete!")

def restore():
    """JSON 파일에서 데이터를 읽어 DB로 복구합니다."""
    app = create_app()
    with app.app_context():
        print(f"🚀 Starting Restore from {BACKUP_DIR}...")
        
        if not os.path.exists(BACKUP_DIR):
            print("❌ Backup directory not found!")
            return

        # 테이블 생성 (혹시 없으면)
        db.create_all()
        
        # 파일 목록
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
        
        for file in files:
            table_name = file.replace(".json", "")
            try:
                print(f"♻️ Restoring table: {table_name}")
                file_path = os.path.join(BACKUP_DIR, file)
                
                df = pd.read_json(file_path, orient="records")
                
                if df.empty:
                    print(f"⚠️ Skipping empty table: {table_name}")
                    continue

                # 데이터 넣기 (append 모드)
                # 주의: 중복 방지를 위해 기존 데이터를 지울지 결정해야 함. 
                # 여기서는 'append'로 하되, 중복 에러가 날 수 있음.
                # 안전하게 하려면 truncate 먼저 하는 게 좋음.
                with db.engine.connect() as conn:
                    # Oracle Truncate or Delete
                    conn.execute(text(f"DELETE FROM {table_name}"))
                    conn.commit()
                
                df.to_sql(table_name, db.engine, if_exists="append", index=False)
                print(f"✅ Restored {len(df)} rows.")
                
            except Exception as e:
                print(f"❌ Failed to restore {table_name}: {e}")
                
        print("🎉 Restore Complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_data.py [backup|restore|seed]")
        sys.exit(1)
        
    command = sys.argv[1]
    if command == "backup":
        backup()
    elif command == "restore":
        restore()
    elif command == "seed":
        print("🌱 Seeding Database from CSV...")
        try:
            # Import logic from the existing script
            # We assume the project structure allows this import
            from belong.ml.load_elderly_stats_from_csv import main as seed_main
            seed_main()
            print("✅ Seeding Complete!")
        except Exception as e:
            print(f"❌ Seeding Failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Unknown command. Use 'backup' or 'restore'.")
