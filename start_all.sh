#!/bin/bash
echo "🚀 Starting Belong All-in-One Pod..."

# ✅ Graceful Shutdown Handler (Backup before exit)
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal. Performing final backup..."
    /app/scripts/backup_db.sh || echo "⚠️ Final backup failed"
    echo "✅ Final backup complete. Shutting down services..."
    
    # Stop PostgreSQL cleanly
    /etc/init.d/postgresql stop 2>/dev/null || true
    
    echo "👋 Shutdown complete."
    exit 0
}

trap cleanup SIGTERM SIGINT

# 0. PostgreSQL 데이터 영속화 (Network Volume)
echo "💾 Setting up PostgreSQL persistence..."
PG_DATA_DIR="/var/lib/postgresql/15/main"
WORKSPACE_PG_DIR="/workspace/pg_data"

# /workspace가 마운트되어 있는지 확인
if [ -d "/workspace" ]; then
    mkdir -p "$WORKSPACE_PG_DIR"
    
    # 이미 심볼릭 링크가 아닌 경우에만 처리
    if [ ! -L "$PG_DATA_DIR" ]; then
        echo "📦 Migrating PostgreSQL data to /workspace..."
        
        # 기존 데이터가 있으면 복사
        if [ -d "$PG_DATA_DIR" ]; then
            if cp -a "$PG_DATA_DIR"/* "$WORKSPACE_PG_DIR/"; then
                echo "✅ PostgreSQL data copied successfully"
                rm -rf "$PG_DATA_DIR"
            else
                echo "⚠️ Failed to copy PostgreSQL data, using original location"
            fi
        fi
        
        # 심볼릭 링크 생성 (원본 삭제된 경우만)
        if [ ! -d "$PG_DATA_DIR" ]; then
            ln -s "$WORKSPACE_PG_DIR" "$PG_DATA_DIR"
            chown -R postgres:postgres "$WORKSPACE_PG_DIR"
            echo "✅ PostgreSQL persistence configured (symlink created)"
        fi
    else
        echo "✅ PostgreSQL persistence already configured (symlink exists)"
        # 심볼릭 링크 대상 확인
        ls -la "$PG_DATA_DIR"
    fi
else
    echo "⚠️ /workspace not mounted, PostgreSQL data will not persist!"
fi

# 1. Initialize & Start PostgreSQL (Local All-in-One)
echo "🐘 Starting PostgreSQL..."
# Use init.d instead of service for better compatibility
/etc/init.d/postgresql start

# Wait loop for PG to be ready (Force IPv4 check)
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h 127.0.0.1 -p 5432 -U postgres; do
  echo "   Waiting for postgres..."
  sleep 2
done

# Setup DB (Idempotent & Force Password)
echo "🔧 Configuring Database..."
# 1. Create user if not exists (ignore error if exists)
su - postgres -c "psql -c \"CREATE USER belong;\"" || true
# 2. FORCE reset password (ensure it matches config)
su - postgres -c "psql -c \"ALTER USER belong WITH PASSWORD 'belong';\""
# 3. Create DB and Grant
su - postgres -c "psql -c \"CREATE DATABASE belong_db OWNER belong;\"" || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE belong_db TO belong;\"" || true

# Set ENV for Flask to use this local DB (Variable name must match config.py)
# Use 127.0.0.1 to avoid IPv6 ::1 connection issues
export DATABASE_URI="postgresql://belong:belong@127.0.0.1:5432/belong_db"

# 2.5. Auto-Restore from Workspace (If backup exists)
LATEST_BACKUP="/workspace/db_backup/latest"
if [ -d "$LATEST_BACKUP" ]; then
    echo "📦 Found backup at $LATEST_BACKUP, restoring..."
    
    # Restore ChromaDB
    if [ -d "$LATEST_BACKUP/chroma_db" ]; then
        rm -rf /app/chroma_db 2>/dev/null || true
        cp -r "$LATEST_BACKUP/chroma_db" /app/chroma_db
        echo "✅ ChromaDB restored"
    fi
    
    # Restore PostgreSQL (only if dump exists)
    if [ -f "$LATEST_BACKUP/belong_db.dump" ]; then
        echo "📥 Restoring PostgreSQL from backup..."
        export PGPASSWORD='belong'
        if pg_restore -h 127.0.0.1 -U belong -d belong_db --no-owner --clean --if-exists "$LATEST_BACKUP/belong_db.dump" 2>&1; then
            echo "✅ PostgreSQL restored from backup successfully"
        else
            echo "⚠️ PostgreSQL restore completed with warnings (may be normal)"
        fi
        unset PGPASSWORD
        
        # 복원 확인
        USER_COUNT=$(psql -h 127.0.0.1 -U belong -d belong_db -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
        echo "📊 Users in database after restore: $USER_COUNT"
    fi
    
    # Restore fine-tuned models
    if [ -d "$LATEST_BACKUP/fine_tune" ]; then
        mkdir -p /app/belong/ml/fine_tune
        cp -r "$LATEST_BACKUP/fine_tune"/* /app/belong/ml/fine_tune/ 2>/dev/null || true
        echo "✅ Models restored"
    fi
    
    echo "✅ Auto-restore complete!"
else
    echo "📋 No backup found at $LATEST_BACKUP, starting fresh..."
fi

# 3. Seed Data (Always run - it will skip if data already exists)
echo "💾 Seeding Database..."
python seed_data.py || echo "⚠️ Seeding failed or skipped"

# 2. Start AI Inference Server (Background)
# 2. Start AI Inference Server (Background)
# Logging to stdout for easier debugging in RunPod Console
echo "🧠 Starting AI Inference Server (Port 8000)..."
uvicorn inference_server.main:app --host 0.0.0.0 --port 8000 &
AI_PID=$!
echo "✅ AI Server started with PID $AI_PID"

# 3. Wait for AI server to init
# (Model loading takes time, so we just wait a bit, but real readiness is async)
echo "⏳ Waiting 10s for AI Server process to settle..."
sleep 10

# Check if process is still alive
if ! kill -0 $AI_PID > /dev/null 2>&1; then
    echo "❌ AI Server exited unexpectedly! Check logs above."
    # We don't exit here to allow Web Server to start for debugging,
    # but in production we might want to fail.
fi

# ✅ 4. Start Periodic Auto-Backup (Background)
echo "⏰ Starting auto-backup service (every 5 minutes)..."
(
    # Wait 1 minute before first backup (빠른 초기 백업)
    echo "⏰ First backup in 60 seconds..."
    sleep 60
    
    while true; do
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        echo "🔄 [$TIMESTAMP] Auto-backup triggered"
        
        # Backup and create 'latest' symlink
        BACKUP_DIR=$(/app/scripts/backup_db.sh | grep "📁 Location:" | awk '{print $3}')
        if [ -n "$BACKUP_DIR" ]; then
            rm -rf /workspace/db_backup/latest
            ln -s "$BACKUP_DIR" /workspace/db_backup/latest
            echo "✅ [$TIMESTAMP] Auto-backup complete → latest"
        else
            echo "⚠️ [$TIMESTAMP] Auto-backup failed"
        fi
        
        sleep 300
    done
) &
BACKUP_PID=$!
echo "✅ Auto-backup service started with PID $BACKUP_PID"

# 5. Start Web Server (Foreground - keeps container alive)
echo "🌐 Starting Flask Web Server (Port 5000)..."
# Ensure RUNPOD_ENDPOINT_URL points to localhost if not set
export RUNPOD_ENDPOINT_URL=${RUNPOD_ENDPOINT_URL:-"http://127.0.0.1:8000"}

# Using Gunicorn for production-grade serving (300s timeout for AI model loading)
exec gunicorn -w 2 -b 0.0.0.0:5000 --timeout 300 "belong.app:create_app()"
