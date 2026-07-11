#!/bin/bash
# Build Lambda deployment ZIPs
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
DIST_DIR="$PROJECT_ROOT/dist"

echo "🔧 Building Lambda deployment packages..."

# Ensure output/staging directories exist
mkdir -p "$DIST_DIR"
mkdir -p "$PROJECT_ROOT/Layer/python/intro_common"
mkdir -p "$DEPLOY_DIR/ui-lambda" "$DEPLOY_DIR/worker-lambda"

# Sync common code to layer and deploy folders
echo "📁 Syncing intro_common..."
cp -f "$PROJECT_ROOT/src/common/"*.py "$PROJECT_ROOT/Layer/python/intro_common/"
cp -f "$PROJECT_ROOT/src/ui_lambda/ui_entry.py" "$DEPLOY_DIR/ui-lambda/ui_entry.py"
cp -f "$PROJECT_ROOT/src/worker_lambda/worker_entry.py" "$DEPLOY_DIR/worker-lambda/worker_entry.py"

# Build UI Lambda ZIP
echo "📦 Building ui-lambda.zip..."
(cd "$DEPLOY_DIR/ui-lambda" && zip -r "$DIST_DIR/ui-lambda.zip" .)

# Build Worker Lambda ZIP
echo "📦 Building worker-lambda.zip..."
(cd "$DEPLOY_DIR/worker-lambda" && zip -r "$DIST_DIR/worker-lambda.zip" .)

# Build Layer ZIP
echo "📦 Building layer.zip..."
(cd "$PROJECT_ROOT/Layer" && zip -r "$DIST_DIR/layer-python313-arm64.zip" python)

echo ""
echo "✅ Build complete!"
ls -lh "$DIST_DIR"/*.zip
