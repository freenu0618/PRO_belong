#!/bin/bash
echo "🚀 Starting Belong All-in-One Pod..."

# Graceful Shutdown Handler (Backup before exit)
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal. Performing final backup..."
    /app/scripts/backup_db.sh || echo "⚠️ Final backup failed"
    echo "✅ Final backup complete. Shutting down services..."
    /etc/init.d/postgresql stop 2>/dev/null || true
    echo "👋 Shutdown complete."
    exit 0
}
trap cleanup SIGTERM SIGINT

# 1. Start PostgreSQL
echo "🐘 Starting PostgreSQL..."
/etc/init.d/postgresql start

# Wait for PostgreSQL to be ready
until pg_isready -h localhost; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# 2. Setup Database & User (If not exists)
su - postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='belong'\"" | grep -q 1 || {
    echo "Creating 'belong' user..."
    su - postgres -c "psql -c \"CREATE USER belong WITH PASSWORD 'belong';\""
    su - postgres -c "psql -c \"ALTER USER belong WITH SUPERUSER;\""
}

su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='belong_db'\"" | grep -q 1 || {
    echo "Creating 'belong_db' database..."
    su - postgres -c "psql -c \"CREATE DATABASE belong_db OWNER belong;\""
}

# Export DATABASE_URL for Flask Config
export DATABASE_URL="postgresql://belong:belong@127.0.0.1:5432/belong_db"
export FLASK_APP=belong.app
export FLASK_ENV=production
echo "✅ Database: $DATABASE_URL"

# 3. Restore from Backup (If exists)
LATEST_BACKUP="/workspace/db_backup/latest"
if [ -d "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP/belong_db.dump" ]; then
    echo "🔄 Found backup at $LATEST_BACKUP, restoring..."
    PGPASSWORD=belong pg_restore -h 127.0.0.1 -U belong -d belong_db --clean --if-exists "$LATEST_BACKUP/belong_db.dump" 2>&1 || echo "⚠️ Restore completed with warnings (may be normal)"
    
    # Check user count
    USER_COUNT=$(PGPASSWORD=belong psql -h 127.0.0.1 -U belong -d belong_db -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo "📊 Users in database after restore: $USER_COUNT"
else
    echo "⚠️ No backup found, starting fresh..."
    # ✅ 마이그레이션 대신 db.create_all() 사용 (테이블 순서 문제 해결)
    python -c "
from belong.app import create_app
from belong.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database tables created successfully!')
" || echo "⚠️ Table creation had issues, continuing..."
fi

# 4. Seed Data
echo "🌱 Seeding Database..."
python seed_data.py || echo "⚠️ Seeding failed or skipped"

# 5. Restore ChromaDB (If exists)
if [ -d "$LATEST_BACKUP/chroma_db" ]; then
    echo "🔄 Restoring ChromaDB..."
    mkdir -p /app/chroma_db
    cp -r "$LATEST_BACKUP/chroma_db"/* /app/chroma_db/ 2>/dev/null || true
fi

# 6. Restore Fine-tuned Models (If exists)
if [ -d "$LATEST_BACKUP/fine_tune" ]; then
    echo "🔄 Restoring Fine-tuned models..."
    mkdir -p /app/belong/ml/fine_tune
    cp -r "$LATEST_BACKUP/fine_tune"/* /app/belong/ml/fine_tune/ 2>/dev/null || true
fi

# 7. Start AI Inference Server (Background)
echo "🤖 Starting AI Inference Server (Port 8000)..."
# Use module path instead of changing directory (more reliable)
nohup python -m uvicorn inference_server.main:app --host 0.0.0.0 --port 8000 --workers 1 > /app/ai_server.log 2>&1 &
AI_PID=$!
echo "✅ AI Server started with PID $AI_PID"

# Wait for AI server to be ready (health check)
echo "⏳ Waiting for AI Server to be ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "✅ AI Server is responding!"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

# 8. Start Auto-Backup Service (Background)
echo "💾 Starting Auto-Backup Service..."
(
    while true; do
        sleep 300
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="/workspace/db_backup/$TIMESTAMP"
        mkdir -p "$BACKUP_DIR"
        
        # Backup PostgreSQL
        PGPASSWORD=belong pg_dump -h 127.0.0.1 -U belong -Fc belong_db > "$BACKUP_DIR/belong_db.dump" 2>&1
        
        # Backup ChromaDB
        cp -r /app/chroma_db "$BACKUP_DIR/" 2>/dev/null || true
        
        # Backup Fine-tuned Models
        cp -r /app/belong/ml/fine_tune "$BACKUP_DIR/" 2>/dev/null || true
        
        # Update latest symlink
        rm -rf /workspace/db_backup/latest
        ln -s "$BACKUP_DIR" /workspace/db_backup/latest
        
        echo "✅ [$TIMESTAMP] Auto-backup complete"
    done
) &
BACKUP_PID=$!
echo "✅ Auto-backup service started with PID $BACKUP_PID"

# 9. Start Web Server (Foreground)
echo "🌐 Starting Flask Web Server (Port 5000)..."
export RUNPOD_ENDPOINT_URL=${RUNPOD_ENDPOINT_URL:-"http://127.0.0.1:8000"}
exec gunicorn -w 1 -b 0.0.0.0:5000 --timeout 300 "belong.app:create_app()"
