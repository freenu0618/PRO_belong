#!/bin/bash
# RunPod DB Restore Script
# Usage: ./restore_db.sh [backup_dir]
# Example: ./restore_db.sh /workspace/db_backup/20241222_120000

set -e

BACKUP_DIR="${1:-/workspace/db_backup/latest}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    echo "Usage: ./restore_db.sh [backup_dir]"
    echo ""
    echo "Available backups:"
    ls -la /workspace/db_backup/ 2>/dev/null || echo "No backups found"
    exit 1
fi

echo "🔄 Starting Database Restore from: $BACKUP_DIR"

# 1. Restore ChromaDB
echo "🧠 Restoring ChromaDB..."
CHROMA_BACKUP="$BACKUP_DIR/chroma_db"
CHROMA_TARGET="/app/chroma_db"
if [ -d "$CHROMA_BACKUP" ]; then
    rm -rf "$CHROMA_TARGET" 2>/dev/null || true
    cp -r "$CHROMA_BACKUP" "$CHROMA_TARGET"
    echo "✅ ChromaDB restored"
else
    echo "⚠️ No ChromaDB backup found, skipping..."
fi

# 2. Restore PostgreSQL
echo "🐘 Restoring PostgreSQL..."
PG_BACKUP="$BACKUP_DIR/belong_db.dump"
if [ -f "$PG_BACKUP" ]; then
    # Drop and recreate database
    su - postgres -c "psql -c 'DROP DATABASE IF EXISTS belong_db;'" || true
    su - postgres -c "psql -c 'CREATE DATABASE belong_db OWNER belong;'" || true
    
    # Restore from dump
    pg_restore -h 127.0.0.1 -U belong -d belong_db "$PG_BACKUP" || {
        echo "⚠️ pg_restore had some warnings (this is often normal)"
    }
    echo "✅ PostgreSQL restored"
else
    echo "⚠️ No PostgreSQL backup found, skipping..."
fi

# 3. Restore Fine-tuned Models
echo "🤖 Restoring Fine-tuned models..."
MODELS_BACKUP="$BACKUP_DIR/fine_tune"
MODELS_TARGET="/app/belong/ml/fine_tune"
if [ -d "$MODELS_BACKUP" ]; then
    mkdir -p "$MODELS_TARGET"
    cp -r "$MODELS_BACKUP"/* "$MODELS_TARGET"/ 2>/dev/null || true
    echo "✅ Models restored"
else
    echo "⚠️ No models backup found, skipping..."
fi

echo ""
echo "✅ Restore Complete!"
echo "💡 Restart the application to apply changes:"
echo "   supervisorctl restart all"
echo "   OR restart the Pod"
