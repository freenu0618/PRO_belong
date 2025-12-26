#!/bin/bash
# RunPod DB Backup Script
# Usage: ./backup_db.sh
# This will backup ChromaDB and PostgreSQL to /workspace/db_backup/

set -e

BACKUP_DIR="/workspace/db_backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "?”„ Starting Database Backup..."
echo "?“ Backup directory: $BACKUP_DIR"

# 1. Backup ChromaDB (Vector Store)
echo "?§  Backing up ChromaDB..."
CHROMA_DIR="/app/chroma_db"
if [ -d "$CHROMA_DIR" ]; then
    cp -r "$CHROMA_DIR" "$BACKUP_DIR/chroma_db"
    echo "??ChromaDB backup complete"
else
    echo "? ï¸ ChromaDB directory not found at $CHROMA_DIR"
fi

# 2. Backup PostgreSQL
echo "?˜ Backing up PostgreSQL..."
export PGPASSWORD='belong'
pg_dump -h 127.0.0.1 -U belong -d belong_db -F c -f "$BACKUP_DIR/belong_db.dump"
unset PGPASSWORD
echo "??PostgreSQL backup complete"

# 3. Backup Fine-tuned Models (Optional - Large)
echo "?¤– Backing up Fine-tuned models..."
MODELS_DIR="/app/belong/ml/fine_tune"
if [ -d "$MODELS_DIR" ]; then
    cp -r "$MODELS_DIR" "$BACKUP_DIR/fine_tune"
    echo "??Models backup complete"
else
    echo "? ï¸ Models directory not found"
fi

# 4. Create manifest
echo "?“‹ Creating backup manifest..."
cat > "$BACKUP_DIR/manifest.txt" << EOF
Belong RunPod Backup
====================
Date: $(date)
Contents:
- chroma_db/: ChromaDB vector store
- belong_db.dump: PostgreSQL database dump
- fine_tune/: Fine-tuned model adapters
EOF

echo ""
echo "??Backup Complete!"
echo "?“ Location: $BACKUP_DIR"
echo ""
echo "?’¡ To download, use RunPod file browser or:"
echo "   rsync -avz root@<pod-ip>:$BACKUP_DIR ./local_backup"
